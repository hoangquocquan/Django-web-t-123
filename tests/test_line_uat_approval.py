"""Safety and state-transition tests for the n8n + LINE UAT demo."""

import pytest
from apps.ai_agent import line_uat_views
from apps.ai_agent.models import OutboundMessageApproval
from apps.ai_agent.services.line_uat import LineUATApprovalService, LineUATError
from apps.foundation.models import FoundationPermission, FoundationRole
from apps.foundation.services import FoundationAuthService, FoundationUserService
from django.test import override_settings


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

    def push(self, *, recipient, message, token):
        self.calls.append({"recipient": recipient, "message": message, "token": token})
        if self.fail:
            raise LineUATError("provider_failed", "Synthetic provider failure.")
        return "uat-request-001", {"http_status": 200, "body": {}}


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
    service.approve(approval.pk, user=user)
    OutboundMessageApproval.objects.filter(pk=approval.pk).update(
        recipient_ref="NOT-ALLOWLISTED"
    )

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
