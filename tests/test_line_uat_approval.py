"""Safety and state-transition tests for the n8n + LINE UAT demo."""

import importlib.util
import io
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from urllib import error as urllib_error

import pytest
from apps.ai_agent import line_uat_views
from apps.ai_agent.models import OutboundMessageApproval
from apps.ai_agent.services import line_uat as line_uat_service
from apps.ai_agent.services.line_uat import (
    LineProviderClient,
    LineUATApprovalService,
    LineUATError,
)
from apps.foundation.models import (
    FoundationAuthToken,
    FoundationPermission,
    FoundationRole,
)
from apps.foundation.services import FoundationAuthService, FoundationUserService
from config.settings.base import env_strict_true
from django.test import override_settings

WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1]
    / "automation"
    / "n8n"
    / "line_uat_approval_demo.json"
)


def _load_line_uat_helper(module_name):
    helper_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "line_uat"
        / f"{module_name}.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, helper_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FakeAI:
    def analyze(self, payload, user=None):
        assert payload["material"] == "SUS304"
        assert user is not None
        return {
            "status": "SUPPORTED",
            "priority": "HIGH",
            "recommended_next_action": "REVIEW_PRODUCT_MATCH",
            "human_approval_required": True,
            "autonomous_action": False,
        }


class RecordingProvider:
    def __init__(self, *, fail=False):
        self.calls = []
        self.fail = fail

    def push(self, *, recipient, message, token, retry_key):
        self.calls.append(
            {
                "recipient": recipient,
                "message": message,
                "token": token,
                "retry_key": retry_key,
            }
        )
        if self.fail:
            raise LineUATError("provider_failed", "Synthetic provider failure.")
        return "uat-request-001", {"http_status": 200, "body": {}}


class BlockingProvider(RecordingProvider):
    def __init__(self):
        super().__init__()
        self.entered = Event()
        self.release = Event()

    def push(self, **kwargs):
        self.calls.append(kwargs)
        self.entered.set()
        assert self.release.wait(timeout=5)
        return "uat-request-concurrent", {"http_status": 200, "body": {}}


def _grant(role_name):
    role, _created = FoundationRole.objects.get_or_create(name=role_name)
    permissions = [("ai_sales", "read"), ("sales", "read"), ("line_uat", "read")]
    if role_name.casefold() in {"manager", "admin"}:
        permissions.append(("line_uat", "approve"))
    for module, action in permissions:
        permission, _created = FoundationPermission.objects.get_or_create(
            code=f"{module}:{action}",
            defaults={"module": module, "action": action},
        )
        role.permissions.add(permission)
    return role


def _user(role_name, email):
    _grant(role_name)
    return FoundationUserService().create_user(
        email=email,
        full_name=role_name.title(),
        password="SecurePass123!",
        role_name=role_name,
    )


def _headers(user):
    token, _row = FoundationAuthService().login(user.email, "SecurePass123!")
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def _draft(user):
    return LineUATApprovalService(ai_sales=FakeAI()).create_draft(
        rfq_id="UAT-RFQ-001",
        synthetic=True,
        environment="uat",
        user=user,
    )


@pytest.mark.django_db
@override_settings(LINE_UAT_RECIPIENT_USER_ID="UAT-LINE-USER-001")
def test_draft_creates_pending_synthetic_uat_record():
    user = _user("sales", "line-draft@example.com")
    approval = _draft(user)

    assert approval.status == "PENDING"
    assert approval.synthetic is True
    assert approval.environment == "uat"
    assert approval.recipient_ref == "UAT-LINE-USER-001"
    assert approval.ai_payload["analysis"]["autonomous_action"] is False
    assert approval.send_attempted is False


@pytest.mark.django_db
@override_settings(
    LINE_SEND_ENABLED=True,
    LINE_UAT_CHANNEL_ACCESS_TOKEN="super-secret-token",
    LINE_UAT_RECIPIENT_USER_ID="UAT-LINE-USER-001",
)
def test_pending_cannot_send():
    user = _user("admin", "line-pending@example.com")
    provider = RecordingProvider()
    approval = _draft(user)

    with pytest.raises(LineUATError, match="Only APPROVED"):
        LineUATApprovalService(provider=provider).send(approval.pk, user=user)

    assert provider.calls == []


@pytest.mark.django_db
@override_settings(
    LINE_SEND_ENABLED=True,
    LINE_UAT_CHANNEL_ACCESS_TOKEN="super-secret-token",
    LINE_UAT_RECIPIENT_USER_ID="UAT-LINE-USER-001",
)
def test_rejected_cannot_send_and_records_no_attempt():
    user = _user("admin", "line-rejected@example.com")
    provider = RecordingProvider()
    approval = _draft(user)
    service = LineUATApprovalService(provider=provider)
    service.reject(approval.pk, user=user, reason="UAT reviewer rejected")

    with pytest.raises(LineUATError, match="Only APPROVED"):
        service.send(approval.pk, user=user)

    approval.refresh_from_db()
    assert approval.status == "REJECTED"
    assert approval.line_result_status == "REJECTED_NO_SEND"
    assert approval.send_attempted is False
    assert provider.calls == []


@pytest.mark.django_db
@override_settings(
    LINE_SEND_ENABLED=True,
    LINE_UAT_CHANNEL_ACCESS_TOKEN="super-secret-token",
    LINE_UAT_RECIPIENT_USER_ID="UAT-LINE-USER-001",
)
def test_approved_message_sends_once_and_retry_is_idempotent():
    user = _user("manager", "line-approved@example.com")
    provider = RecordingProvider()
    approval = _draft(user)
    service = LineUATApprovalService(provider=provider)
    service.approve(approval.pk, user=user)

    first = service.send(approval.pk, user=user)
    second = service.send(approval.pk, user=user)

    assert first.status == "SENT"
    assert second.status == "SENT"
    assert first.provider_message_id == "uat-request-001"
    assert len(provider.calls) == 1
    assert provider.calls[0]["retry_key"] == str(approval.pk)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("synthetic", "environment", "code"),
    [(False, "uat", "synthetic_required"), (True, "production", "uat_only")],
)
def test_draft_rejects_non_synthetic_or_non_uat(synthetic, environment, code):
    user = _user("sales", f"line-invalid-{code}@example.com")

    with pytest.raises(LineUATError) as exc_info:
        LineUATApprovalService(ai_sales=FakeAI()).create_draft(
            rfq_id="UAT-RFQ-001",
            synthetic=synthetic,
            environment=environment,
            user=user,
        )

    assert exc_info.value.code == code


@pytest.mark.django_db
def test_uat_api_rejects_non_synthetic_and_non_uat_payloads(client, monkeypatch):
    sales = _user("sales", "line-invalid-api@example.com")
    monkeypatch.setattr(
        line_uat_views,
        "LineUATApprovalService",
        lambda: LineUATApprovalService(ai_sales=FakeAI()),
    )

    responses = [
        client.post(
            "/api/v1/internal/line-uat/drafts/",
            data={"rfq_id": "UAT-RFQ-001", "synthetic": False, "environment": "uat"},
            content_type="application/json",
            **_headers(sales),
        ),
        client.post(
            "/api/v1/internal/line-uat/drafts/",
            data={"rfq_id": "UAT-RFQ-001", "synthetic": True, "environment": "prod"},
            content_type="application/json",
            **_headers(sales),
        ),
    ]

    assert [response.status_code for response in responses] == [400, 400]
    assert [response.json()["error"]["code"] for response in responses] == [
        "synthetic_required",
        "uat_only",
    ]
    assert OutboundMessageApproval.objects.count() == 0


@pytest.mark.django_db
@override_settings(
    LINE_SEND_ENABLED=True,
    LINE_UAT_CHANNEL_ACCESS_TOKEN="super-secret-token",
    LINE_UAT_RECIPIENT_USER_ID="UAT-LINE-USER-001",
)
def test_recipient_outside_allowlist_is_rejected():
    user = _user("admin", "line-allowlist@example.com")
    provider = RecordingProvider()
    approval = _draft(user)
    service = LineUATApprovalService(provider=provider)
    OutboundMessageApproval.objects.filter(pk=approval.pk).update(
        recipient_ref="NOT-ALLOWLISTED"
    )
    service.approve(approval.pk, user=user)

    with pytest.raises(LineUATError) as exc_info:
        service.send(approval.pk, user=user)

    assert exc_info.value.code == "recipient_not_allowlisted"
    assert provider.calls == []


@pytest.mark.django_db
@override_settings(
    LINE_SEND_ENABLED=False,
    LINE_UAT_CHANNEL_ACCESS_TOKEN="super-secret-token",
    LINE_UAT_RECIPIENT_USER_ID="UAT-LINE-USER-001",
)
def test_kill_switch_prevents_provider_request():
    user = _user("admin", "line-disabled@example.com")
    provider = RecordingProvider()
    approval = _draft(user)
    service = LineUATApprovalService(provider=provider)
    service.approve(approval.pk, user=user)

    result = service.send(approval.pk, user=user)

    assert result.status == "APPROVED"
    assert result.line_result_status == "SEND_DISABLED"
    assert result.provider_response == {"mode": "DRY_RUN", "send_attempted": False}
    assert provider.calls == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "malformed_value", ["false", "False", "TRUE", "true", "1", 1, None, "random"]
)
@override_settings(
    LINE_UAT_CHANNEL_ACCESS_TOKEN="super-secret-token",
    LINE_UAT_RECIPIENT_USER_ID="UAT-LINE-USER-001",
)
def test_kill_switch_accepts_only_literal_boolean_true(malformed_value, settings):
    settings.LINE_SEND_ENABLED = malformed_value
    user = _user("admin", f"line-switch-{malformed_value!s}@example.com")
    provider = RecordingProvider()
    approval = _draft(user)
    service = LineUATApprovalService(provider=provider)
    service.approve(approval.pk, user=user)

    result = service.send(approval.pk, user=user)

    assert result.line_result_status == "SEND_DISABLED"
    assert result.send_attempted is False
    assert provider.calls == []


@pytest.mark.django_db
@override_settings(
    LINE_SEND_ENABLED=False,
    LINE_UAT_CHANNEL_ACCESS_TOKEN="",
    LINE_UAT_RECIPIENT_USER_ID="",
)
def test_dry_run_does_not_require_recipient_or_token():
    user = _user("admin", "line-dry-run-empty-config@example.com")
    provider = RecordingProvider()
    approval = _draft(user)
    service = LineUATApprovalService(provider=provider)
    service.approve(approval.pk, user=user)

    result = service.send(approval.pk, user=user)

    assert result.line_result_status == "SEND_DISABLED"
    assert result.send_attempted is False
    assert provider.calls == []


@pytest.mark.django_db
@override_settings(
    LINE_SEND_ENABLED=True,
    LINE_UAT_CHANNEL_ACCESS_TOKEN="super-secret-token",
    LINE_UAT_RECIPIENT_USER_ID="",
)
def test_enabled_send_requires_nonempty_allowlisted_recipient():
    user = _user("admin", "line-empty-recipient@example.com")
    provider = RecordingProvider()
    approval = _draft(user)
    service = LineUATApprovalService(provider=provider)
    service.approve(approval.pk, user=user)

    with pytest.raises(LineUATError) as exc_info:
        service.send(approval.pk, user=user)

    assert exc_info.value.code == "recipient_not_allowlisted"
    assert provider.calls == []


@pytest.mark.django_db
@override_settings(
    LINE_SEND_ENABLED=True,
    LINE_UAT_CHANNEL_ACCESS_TOKEN="super-secret-token",
    LINE_UAT_RECIPIENT_USER_ID="UAT-LINE-USER-001",
)
def test_message_change_after_approval_is_blocked():
    user = _user("admin", "line-mutated-message@example.com")
    provider = RecordingProvider()
    approval = _draft(user)
    service = LineUATApprovalService(provider=provider)
    service.approve(approval.pk, user=user)
    OutboundMessageApproval.objects.filter(pk=approval.pk).update(
        proposed_message="Different text after approval"
    )

    with pytest.raises(LineUATError) as exc_info:
        service.send(approval.pk, user=user)

    assert exc_info.value.code == "approved_content_changed"
    assert provider.calls == []


@pytest.mark.django_db
@override_settings(
    LINE_SEND_ENABLED=True,
    LINE_UAT_CHANNEL_ACCESS_TOKEN="super-secret-token",
    LINE_UAT_RECIPIENT_USER_ID="UAT-LINE-USER-001",
)
def test_recipient_and_allowlist_change_after_approval_is_blocked(settings):
    user = _user("admin", "line-mutated-recipient@example.com")
    provider = RecordingProvider()
    approval = _draft(user)
    service = LineUATApprovalService(provider=provider)
    service.approve(approval.pk, user=user)
    OutboundMessageApproval.objects.filter(pk=approval.pk).update(
        recipient_ref="SECOND-UAT-USER"
    )
    settings.LINE_UAT_RECIPIENT_USER_ID = "SECOND-UAT-USER"

    with pytest.raises(LineUATError) as exc_info:
        service.send(approval.pk, user=user)

    assert exc_info.value.code == "approved_content_changed"
    assert provider.calls == []


@pytest.mark.django_db
@override_settings(
    LINE_SEND_ENABLED=True,
    LINE_UAT_CHANNEL_ACCESS_TOKEN="super-secret-token",
    LINE_UAT_RECIPIENT_USER_ID="UAT-LINE-USER-001",
)
def test_provider_failure_records_failed_without_secret():
    user = _user("admin", "line-failed@example.com")
    provider = RecordingProvider(fail=True)
    approval = _draft(user)
    service = LineUATApprovalService(provider=provider)
    service.approve(approval.pk, user=user)

    result = service.send(approval.pk, user=user)

    assert result.status == "FAILED"
    assert result.send_attempted is True
    assert result.line_result_status == "FAILED"
    assert result.provider_response == {"error_code": "provider_failed"}
    assert "super-secret-token" not in str(result.provider_response)
    assert "super-secret-token" not in str(result.audit_log)


@pytest.mark.django_db
@override_settings(LINE_UAT_RECIPIENT_USER_ID="UAT-LINE-USER-001")
def test_unauthorized_user_cannot_approve(client):
    sales = _user("sales", "line-sales@example.com")
    approval = _draft(sales)

    anonymous = client.post(
        f"/api/v1/internal/line-uat/approvals/{approval.pk}/approve/",
        data={},
        content_type="application/json",
    )
    sales_response = client.post(
        f"/api/v1/internal/line-uat/approvals/{approval.pk}/approve/",
        data={},
        content_type="application/json",
        **_headers(sales),
    )

    assert anonymous.status_code == 403
    assert sales_response.status_code == 403
    approval.refresh_from_db()
    assert approval.status == "PENDING"


@pytest.mark.django_db
@override_settings(
    LINE_SEND_ENABLED=False,
    LINE_UAT_CHANNEL_ACCESS_TOKEN="super-secret-token",
    LINE_UAT_RECIPIENT_USER_ID="UAT-LINE-USER-001",
)
def test_api_responses_never_expose_line_token(client, monkeypatch):
    manager = _user("manager", "line-api@example.com")
    monkeypatch.setattr(
        line_uat_views,
        "LineUATApprovalService",
        lambda: LineUATApprovalService(ai_sales=FakeAI()),
    )
    draft = client.post(
        "/api/v1/internal/line-uat/drafts/",
        data={"rfq_id": "UAT-RFQ-001", "synthetic": True, "environment": "uat"},
        content_type="application/json",
        **_headers(manager),
    )
    approval_id = draft.json()["data"]["approval_id"]
    approve = client.post(
        f"/api/v1/internal/line-uat/approvals/{approval_id}/approve/",
        data={},
        content_type="application/json",
        **_headers(manager),
    )
    send = client.post(
        f"/api/v1/internal/line-uat/approvals/{approval_id}/send/",
        data={},
        content_type="application/json",
        **_headers(manager),
    )

    assert draft.status_code == 201
    assert approve.status_code == 200
    assert send.status_code == 200
    assert "super-secret-token" not in draft.content.decode()
    assert "super-secret-token" not in approve.content.decode()
    assert "super-secret-token" not in send.content.decode()


@pytest.mark.django_db
@override_settings(LINE_UAT_RECIPIENT_USER_ID="UAT-LINE-USER-001")
def test_sales_and_anonymous_cannot_call_send_endpoint(client):
    admin = _user("admin", "line-send-admin@example.com")
    sales = _user("sales", "line-send-sales@example.com")
    approval = _draft(admin)
    LineUATApprovalService().approve(approval.pk, user=admin)
    url = f"/api/v1/internal/line-uat/approvals/{approval.pk}/send/"

    anonymous = client.post(url, data={}, content_type="application/json")
    sales_response = client.post(
        url,
        data={},
        content_type="application/json",
        **_headers(sales),
    )

    assert anonymous.status_code == 403
    assert sales_response.status_code == 403


@pytest.mark.django_db
@override_settings(LINE_UAT_RECIPIENT_USER_ID="UAT-LINE-USER-001")
def test_approval_and_rejection_are_one_way_transitions():
    user = _user("admin", "line-one-way@example.com")
    service = LineUATApprovalService(ai_sales=FakeAI())
    approved = _draft(user)
    rejected = _draft(user)

    service.approve(approved.pk, user=user)
    with pytest.raises(LineUATError, match="Only PENDING"):
        service.approve(approved.pk, user=user)
    with pytest.raises(LineUATError, match="Only PENDING"):
        service.reject(approved.pk, user=user)

    service.reject(rejected.pk, user=user)
    with pytest.raises(LineUATError, match="Only PENDING"):
        service.approve(rejected.pk, user=user)


@pytest.mark.django_db
def test_draft_api_rejects_coercion_unknown_fields_and_unknown_rfq(client, monkeypatch):
    sales = _user("sales", "line-strict-input@example.com")
    monkeypatch.setattr(
        line_uat_views,
        "LineUATApprovalService",
        lambda: LineUATApprovalService(ai_sales=FakeAI()),
    )
    payloads = [
        {"rfq_id": "UAT-RFQ-001", "synthetic": "true", "environment": "uat"},
        {"rfq_id": "UAT-RFQ-001", "synthetic": 1, "environment": "uat"},
        {"rfq_id": "UAT-RFQ-001", "synthetic": True, "environment": "UAT"},
        {"rfq_id": "UNKNOWN", "synthetic": True, "environment": "uat"},
        {
            "rfq_id": "UAT-RFQ-001",
            "synthetic": True,
            "environment": "uat",
            "recipient_ref": "attacker-controlled",
        },
        {"rfq_id": "UAT-RFQ-001", "synthetic": True},
        {"rfq_id": None, "synthetic": True, "environment": "uat"},
    ]

    responses = [
        client.post(
            "/api/v1/internal/line-uat/drafts/",
            data=payload,
            content_type="application/json",
            **_headers(sales),
        )
        for payload in payloads
    ]

    assert all(response.status_code == 400 for response in responses)
    assert OutboundMessageApproval.objects.count() == 0


@pytest.mark.django_db
@override_settings(LINE_UAT_RECIPIENT_USER_ID="UAT-LINE-USER-001")
def test_state_endpoints_reject_mass_assignment_fields(client):
    manager = _user("manager", "line-mass-assignment@example.com")
    approval = _draft(manager)

    approve = client.post(
        f"/api/v1/internal/line-uat/approvals/{approval.pk}/approve/",
        data={"status": "SENT", "proposed_message": "changed"},
        content_type="application/json",
        **_headers(manager),
    )
    send = client.post(
        f"/api/v1/internal/line-uat/approvals/{approval.pk}/send/",
        data={"recipient_ref": "attacker-controlled"},
        content_type="application/json",
        **_headers(manager),
    )

    assert approve.status_code == 400
    assert send.status_code == 400
    approval.refresh_from_db()
    assert approval.status == "PENDING"


@pytest.mark.django_db(transaction=True)
@override_settings(
    LINE_SEND_ENABLED=True,
    LINE_UAT_CHANNEL_ACCESS_TOKEN="super-secret-token",
    LINE_UAT_RECIPIENT_USER_ID="UAT-LINE-USER-001",
)
def test_concurrent_retry_observes_committed_claim_and_calls_provider_once():
    user = _user("admin", "line-concurrent@example.com")
    provider = BlockingProvider()
    approval = _draft(user)
    service = LineUATApprovalService(provider=provider)
    service.approve(approval.pk, user=user)

    with ThreadPoolExecutor(max_workers=1) as executor:
        first_future = executor.submit(service.send, approval.pk, user=user)
        assert provider.entered.wait(timeout=5)
        concurrent = service.send(approval.pk, user=user)
        provider.release.set()
        first = first_future.result(timeout=5)

    assert concurrent.line_result_status == "SENDING"
    assert first.status == "SENT"
    assert len(provider.calls) == 1


class FakeHTTPResponse:
    def __init__(self, body=b"{}", status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, limit):
        return self.body[:limit]


def test_provider_uses_retry_key_and_handles_invalid_json(monkeypatch):
    captured = {}

    def fake_urlopen(http_request, timeout):
        captured["headers"] = dict(http_request.header_items())
        captured["timeout"] = timeout
        return FakeHTTPResponse(body=b"not-json", headers={"x-line-request-id": "req-1"})

    monkeypatch.setattr(line_uat_service.request, "urlopen", fake_urlopen)
    request_id, response = LineProviderClient().push(
        recipient="UAT-LINE-USER-001",
        message="synthetic",
        token="super-secret-token",
        retry_key="123e4567-e89b-12d3-a456-426614174000",
    )

    assert request_id == "req-1"
    assert response == {
        "http_status": 200,
        "body": {"unparseable_response": True},
    }
    assert captured["headers"]["X-line-retry-key"] == (
        "123e4567-e89b-12d3-a456-426614174000"
    )
    assert "super-secret-token" not in str(response)


@pytest.mark.parametrize("status_code", [400, 401, 403, 429, 500])
def test_provider_http_failures_are_bounded_and_sanitized(monkeypatch, status_code):
    def raise_http_error(http_request, timeout):
        del http_request, timeout
        raise urllib_error.HTTPError(
            "https://api.line.me/v2/bot/message/push",
            status_code,
            "provider error",
            {},
            io.BytesIO(b'{"message":"bounded provider error"}'),
        )

    monkeypatch.setattr(line_uat_service.request, "urlopen", raise_http_error)
    with pytest.raises(LineUATError) as exc_info:
        LineProviderClient().push(
            recipient="UAT-LINE-USER-001",
            message="synthetic",
            token="super-secret-token",
            retry_key="123e4567-e89b-12d3-a456-426614174000",
        )

    assert exc_info.value.code == "provider_failed"
    assert str(status_code) in exc_info.value.message
    assert "super-secret-token" not in exc_info.value.message


def test_provider_timeout_is_sanitized(monkeypatch):
    def raise_timeout(http_request, timeout):
        del http_request, timeout
        raise TimeoutError("super-secret-token must not escape")

    monkeypatch.setattr(line_uat_service.request, "urlopen", raise_timeout)
    with pytest.raises(LineUATError) as exc_info:
        LineProviderClient().push(
            recipient="UAT-LINE-USER-001",
            message="synthetic",
            token="super-secret-token",
            retry_key="123e4567-e89b-12d3-a456-426614174000",
        )

    assert exc_info.value.code == "provider_failed"
    assert "super-secret-token" not in exc_info.value.message


def test_provider_409_is_treated_as_deduplicated_success(monkeypatch):
    def raise_conflict(http_request, timeout):
        del http_request, timeout
        raise urllib_error.HTTPError(
            "https://api.line.me/v2/bot/message/push",
            409,
            "already accepted",
            {"x-line-accepted-request-id": "accepted-1"},
            io.BytesIO(b'{"message":"already accepted"}'),
        )

    monkeypatch.setattr(line_uat_service.request, "urlopen", raise_conflict)
    request_id, response = LineProviderClient().push(
        recipient="UAT-LINE-USER-001",
        message="synthetic",
        token="super-secret-token",
        retry_key="123e4567-e89b-12d3-a456-426614174000",
    )

    assert request_id == "accepted-1"
    assert response == {"http_status": 409, "deduplicated": True}


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        (None, False),
        ("", False),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("0", False),
        ("1", False),
        ("yes", False),
        ("on", False),
        ("random", False),
        ("true", True),
        (" TRUE ", True),
    ],
)
def test_line_send_environment_parser_is_fail_closed(monkeypatch, raw_value, expected):
    if raw_value is None:
        monkeypatch.delenv("LINE_SEND_ENABLED", raising=False)
    else:
        monkeypatch.setenv("LINE_SEND_ENABLED", raw_value)

    assert env_strict_true("LINE_SEND_ENABLED") is expected


def test_n8n_workflow_has_no_direct_line_call_or_embedded_credentials():
    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
    workflow = json.loads(workflow_text)

    assert "api.line.me" not in workflow_text
    assert "LINE_UAT_CHANNEL_ACCESS_TOKEN" not in workflow_text
    assert "LINE_UAT_CHANNEL_SECRET" not in workflow_text
    assert workflow["active"] is False
    assert all(
        node["type"] != "n8n-nodes-base.line"
        for node in workflow["nodes"]
    )


def test_runtime_workflow_builder_adds_fail_closed_send_interlock(tmp_path):
    import sys

    builder = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "line_uat"
        / "build_live_workflow.py"
    )
    destination = tmp_path / "runtime-workflow.json"
    subprocess.run(
        [sys.executable, str(builder), str(WORKFLOW_PATH), str(destination)],
        check=True,
        capture_output=True,
        text=True,
    )

    runtime_text = destination.read_text(encoding="utf-8")
    runtime = json.loads(runtime_text)
    nodes = {node["name"]: node for node in runtime["nodes"]}
    connections = runtime["connections"]

    assert runtime["active"] is False
    assert "api.line.me" not in runtime_text
    assert "LINE_UAT_CHANNEL_ACCESS_TOKEN" not in runtime_text
    assert nodes["Final Runtime Send Interlock"]["type"] == "n8n-nodes-base.wait"
    assert connections["Verify APPROVED Safety State"]["main"][0][0]["node"] == (
        "Final Runtime Send Interlock"
    )
    assert connections["Final Runtime Send Interlock"]["main"][0][0]["node"] == (
        "Django Kill Switch + LINE Send"
    )
    send_url = nodes["Django Kill Switch + LINE Send"]["parameters"]["url"]
    assert "$('Verify APPROVED Safety State').item.json.approval_id" in send_url


def test_n8n_cli_resolver_uses_explicit_override_without_appdata_assumption(tmp_path):
    resolver = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "line_uat"
        / "N8nCliResolver.psm1"
    )
    fake_cli = tmp_path / "n8n.cmd"
    fake_cli.write_text(
        '@echo off\r\nif "%~1"=="--version" echo 2.37.10\r\n',
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment.update(
        {
            "N8N_RESOLVER_MODULE": str(resolver),
            "N8N_TEST_OVERRIDE": str(fake_cli),
            "N8N_TEST_REPO": str(Path(__file__).resolve().parents[1]),
        }
    )
    command = (
        "Import-Module $env:N8N_RESOLVER_MODULE -Force; "
        "$result = Resolve-N8nCli -Repo $env:N8N_TEST_REPO "
        "-OverridePath $env:N8N_TEST_OVERRIDE; "
        "$result | ConvertTo-Json -Compress"
    )
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    resolved = json.loads(completed.stdout)

    assert resolved["Version"] == "2.37.10"
    assert resolved["Source"] == "override"
    assert Path(resolved["ResolvedPath"]).resolve() == fake_cli.resolve()
    assert "AppData\\Roaming\\npm" not in resolver.read_text(encoding="utf-8")


@pytest.mark.django_db
def test_isolated_uat_foundation_bootstrap_is_minimal_idempotent_and_token_ready():
    bootstrap = _load_line_uat_helper("bootstrap_foundation_uat")
    token_helper = _load_line_uat_helper("create_foundation_token")
    FoundationRole.objects.filter(name=bootstrap.ROLE_NAME).delete()

    role = bootstrap.bootstrap_uat_role()
    required_codes = set(bootstrap.REQUIRED_PERMISSIONS)

    assert role.name == "manager"
    assert role.description == bootstrap.ROLE_DESCRIPTION
    assert role.is_active is True
    assert set(role.permissions.values_list("code", flat=True)) == required_codes
    assert not role.permissions.filter(module="*", action="*").exists()

    role_count = FoundationRole.objects.filter(name=bootstrap.ROLE_NAME).count()
    relation_count = role.permissions.count()
    second = bootstrap.bootstrap_uat_role()

    assert second.pk == role.pk
    assert FoundationRole.objects.filter(name=bootstrap.ROLE_NAME).count() == role_count
    assert second.permissions.count() == relation_count == 4
    assert set(second.permissions.values_list("code", flat=True)) == required_codes

    token_helper.configure_django()
    raw_token, token = token_helper.create_temporary_principal()
    authenticated = FoundationAuthService().authenticate_token(raw_token)

    assert token.pk is not None
    assert token.user_id == authenticated.pk
    assert authenticated.role_id == role.pk
    assert set(authenticated.role.permissions.values_list("code", flat=True)) == (
        required_codes
    )
    assert FoundationAuthToken.objects.filter(pk=token.pk).exists()


def test_n8n_approval_gate_is_explicit_and_reject_branch_cannot_send():
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    nodes = {node["name"]: node for node in workflow["nodes"]}
    connections = workflow["connections"]
    gate = nodes["Explicit APPROVE + UAT Ack?"]["parameters"]["conditions"]
    serialized_gate = json.dumps(gate, sort_keys=True)

    assert '"rightValue": "APPROVE"' in serialized_gate
    assert '"rightValue": true' in serialized_gate
    assert "$json.decision ?? $json.Decision" in serialized_gate
    assert "Array.isArray($json['I confirm this is synthetic UAT data'])" in (
        serialized_gate
    )
    assert gate["combinator"] == "and"
    assert connections["Explicit APPROVE + UAT Ack?"]["main"][0][0]["node"] == (
        "Persist APPROVED"
    )
    assert connections["Explicit APPROVE + UAT Ack?"]["main"][1][0]["node"] == (
        "Persist REJECTED - No Send"
    )
    assert "Persist REJECTED - No Send" not in connections
    assert connections["Verify APPROVED Safety State"]["main"][0][0]["node"] == (
        "Django Kill Switch + LINE Send"
    )


def test_n8n_reject_reason_supports_runtime_form_label_keys():
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    nodes = {node["name"]: node for node in workflow["nodes"]}
    reject_body = nodes["Persist REJECTED - No Send"]["parameters"]["body"]

    assert "$json.review_note" in reject_body
    assert "$json['Review note']" in reject_body


def test_n8n_form_shows_exact_message_and_uat_warning_without_regeneration():
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    nodes = {node["name"]: node for node in workflow["nodes"]}
    description = nodes["Human Approval Gate"]["parameters"]["formDescription"]
    approve_to_send_nodes = {
        "Persist APPROVED",
        "Re-fetch Approval",
        "Verify APPROVED Safety State",
        "Django Kill Switch + LINE Send",
        "Final Audit Output",
    }

    assert "UAT / SYNTHETIC — NO REAL CUSTOMER" in description
    assert "{{ $json.rfq_id }}" in description
    assert "{{ $json.ai_payload.analysis.recommended_next_action }}" in description
    assert "{{ $json.proposed_message }}" in description
    assert all(
        nodes[name]["type"] != "n8n-nodes-base.openAi"
        for name in approve_to_send_nodes
    )


@pytest.mark.django_db
@override_settings(
    LINE_SEND_ENABLED=True,
    LINE_UAT_CHANNEL_ACCESS_TOKEN="super-secret-token",
    LINE_UAT_RECIPIENT_USER_ID="UAT-LINE-USER-001",
)
def test_process_crash_after_claim_cannot_auto_send_again():
    class CrashProvider:
        def __init__(self):
            self.calls = 0

        def push(self, **kwargs):
            del kwargs
            self.calls += 1
            raise RuntimeError("simulated process crash")

    user = _user("admin", "line-crash-window@example.com")
    provider = CrashProvider()
    approval = _draft(user)
    service = LineUATApprovalService(provider=provider)
    service.approve(approval.pk, user=user)

    with pytest.raises(RuntimeError, match="simulated process crash"):
        service.send(approval.pk, user=user)
    retry = service.send(approval.pk, user=user)

    assert retry.status == "APPROVED"
    assert retry.line_result_status == "SENDING"
    assert retry.send_claimed_at is not None
    assert provider.calls == 1
