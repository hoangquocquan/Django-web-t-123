"""Fail-closed service boundary for the synthetic n8n + LINE UAT demo."""

from __future__ import annotations

import json
import secrets
from hashlib import sha256
from urllib import error, request

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.ai_agent.models import OutboundMessageApproval
from apps.ai_agent.services.sales_assistant import SalesAssistantService

UAT_RFQ = {
    "id": "UAT-RFQ-001",
    "environment": "uat",
    "synthetic": True,
    "customer": {"id": "UAT-CUST-001", "name": "UAT Tanaka Manufacturing"},
    "part_name": "SUS304 Precision Bracket",
    "quantity": 100,
    "due_date": "2027-12-01",
    "material": "SUS304",
    "process": "CNC machining",
    "notes": "UAT ONLY - DO NOT CONTACT REAL CUSTOMER",
}


class LineUATError(Exception):
    """Expected safety or state error with a stable API code."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def _audit_event(action, actor="", **details):
    return {
        "action": action,
        "actor": actor,
        "timestamp": timezone.now().isoformat(),
        **details,
    }


def _configured_recipient():
    recipient = getattr(settings, "LINE_UAT_RECIPIENT_USER_ID", "")
    return recipient.strip() if isinstance(recipient, str) else ""


def _approved_content_hash(approval):
    """Fingerprint the exact content and routing fields observed by the reviewer."""
    canonical = json.dumps(
        {
            "channel": approval.channel,
            "environment": approval.environment,
            "message": approval.proposed_message,
            "recipient_ref": approval.recipient_ref,
            "rfq_id": approval.rfq_id,
            "synthetic": approval.synthetic,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


class LineProviderClient:
    """Minimal LINE push adapter that never logs or returns the bearer token."""

    endpoint = "https://api.line.me/v2/bot/message/push"

    def push(self, *, recipient, message, token, retry_key):
        payload = json.dumps(
            {"to": recipient, "messages": [{"type": "text", "text": message}]}
        ).encode("utf-8")
        http_request = request.Request(
            self.endpoint,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Line-Retry-Key": retry_key,
            },
        )
        try:
            with request.urlopen(http_request, timeout=10) as response:
                body = response.read(4096).decode("utf-8", errors="replace")
                try:
                    parsed = json.loads(body) if body else {}
                except json.JSONDecodeError:
                    parsed = {"unparseable_response": True}
                request_id = response.headers.get("x-line-request-id", "")
                return request_id, {
                    "http_status": response.status,
                    "body": parsed,
                }
        except error.HTTPError as exc:
            if exc.code == 409:
                accepted_request_id = exc.headers.get("x-line-accepted-request-id", "")
                return accepted_request_id, {
                    "http_status": 409,
                    "deduplicated": True,
                }
            raise LineUATError(
                "provider_failed", f"LINE provider returned HTTP {exc.code}."
            ) from exc
        except (error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            raise LineUATError("provider_failed", "LINE provider request failed.") from exc


class LineUATApprovalService:
    """Create, decide, and send synthetic LINE drafts under mandatory approval."""

    def __init__(self, *, ai_sales=None, provider=None):
        self.ai_sales = ai_sales or SalesAssistantService()
        self.provider = provider or LineProviderClient()

    def create_draft(self, *, rfq_id, synthetic, environment, user):
        if synthetic is not True:
            raise LineUATError("synthetic_required", "UAT drafts must be synthetic.")
        if environment != "uat":
            raise LineUATError("uat_only", "The LINE demo environment must be uat.")
        if rfq_id != UAT_RFQ["id"]:
            raise LineUATError("unknown_uat_rfq", "Only the bundled synthetic UAT RFQ is allowed.")

        ai_payload = self.ai_sales.analyze(
            {
                "customer_name": UAT_RFQ["customer"]["name"],
                "request": (
                    f"Need {UAT_RFQ['quantity']} {UAT_RFQ['part_name']} parts. "
                    f"{UAT_RFQ['notes']}"
                ),
                "material": UAT_RFQ["material"],
                "quantity": UAT_RFQ["quantity"],
                "process": UAT_RFQ["process"],
                "drawing_available": True,
                "deadline": UAT_RFQ["due_date"],
            },
            user=user,
        )
        ai_payload["human_approval_required"] = True
        ai_payload["autonomous_action"] = False
        proposed_message = self._message(ai_payload)
        recipient = _configured_recipient() or "ENV:LINE_UAT_RECIPIENT_USER_ID"
        approval = OutboundMessageApproval.objects.create(
            environment="uat",
            synthetic=True,
            rfq_id=rfq_id,
            channel="line",
            recipient_ref=recipient,
            proposed_message=proposed_message,
            status=OutboundMessageApproval.Status.PENDING,
            ai_payload={"rfq": UAT_RFQ, "analysis": ai_payload},
            audit_log=[
                _audit_event(
                    "DRAFT_CREATED",
                    user.email,
                    send_attempted=False,
                    warning="UAT / SYNTHETIC — NO REAL CUSTOMER",
                )
            ],
        )
        return approval

    @staticmethod
    def _message(ai_payload):
        next_action = ai_payload.get("recommended_next_action", "HUMAN_REVIEW")
        return (
            "[UAT / SYNTHETIC — NO REAL CUSTOMER]\n"
            "UAT Tanaka Manufacturing 様\n"
            "SUS304 Precision Bracket 100個のお問い合わせありがとうございます。"
            "内容を確認し、担当者よりご案内いたします。\n"
            f"社内確認区分: {next_action}\n"
            "※これはUATテストメッセージです。"
        )

    @transaction.atomic
    def approve(self, approval_id, *, user):
        approval = self._locked(approval_id)
        if approval.status != OutboundMessageApproval.Status.PENDING:
            raise LineUATError("invalid_state", "Only PENDING messages may be approved.")
        approval.status = OutboundMessageApproval.Status.APPROVED
        approval.approved_by = user
        approval.approved_at = timezone.now()
        approval.approved_content_hash = _approved_content_hash(approval)
        approval.audit_log = [*_safe_events(approval), _audit_event("APPROVED", user.email)]
        approval.save(
            update_fields=[
                "status",
                "approved_by",
                "approved_at",
                "approved_content_hash",
                "audit_log",
                "updated_at",
            ]
        )
        return approval

    @transaction.atomic
    def reject(self, approval_id, *, user, reason=""):
        approval = self._locked(approval_id)
        if approval.status != OutboundMessageApproval.Status.PENDING:
            raise LineUATError("invalid_state", "Only PENDING messages may be rejected.")
        approval.status = OutboundMessageApproval.Status.REJECTED
        approval.rejected_by = user
        approval.rejected_at = timezone.now()
        approval.line_result_status = "REJECTED_NO_SEND"
        approval.audit_log = [
            *_safe_events(approval),
            _audit_event("REJECTED", user.email, reason=reason, send_attempted=False),
        ]
        approval.save(
            update_fields=[
                "status",
                "rejected_by",
                "rejected_at",
                "line_result_status",
                "audit_log",
                "updated_at",
            ]
        )
        return approval

    def send(self, approval_id, *, user):
        with transaction.atomic():
            approval = self._locked(approval_id)
            if approval.status == OutboundMessageApproval.Status.SENT:
                return approval
            if approval.status != OutboundMessageApproval.Status.APPROVED:
                raise LineUATError("not_approved", "Only APPROVED messages may be sent.")
            self._validate_uat_invariants(approval)
            self._validate_approved_content(approval)

            if getattr(settings, "LINE_SEND_ENABLED", False) is not True:
                approval.line_result_status = "SEND_DISABLED"
                approval.provider_response = {"mode": "DRY_RUN", "send_attempted": False}
                approval.audit_log = [
                    *_safe_events(approval),
                    _audit_event("SEND_DISABLED", user.email, send_attempted=False),
                ]
                approval.save(
                    update_fields=[
                        "line_result_status",
                        "provider_response",
                        "audit_log",
                        "updated_at",
                    ]
                )
                return approval

            self._validate_recipient(approval)
            token = getattr(settings, "LINE_UAT_CHANNEL_ACCESS_TOKEN", "")
            if not isinstance(token, str) or not token.strip():
                raise LineUATError(
                    "missing_line_token", "LINE UAT access token is not configured."
                )
            token = token.strip()

            if approval.send_claimed_at is not None:
                return approval

            claimed_at = timezone.now()
            claimed_events = [
                *_safe_events(approval),
                _audit_event("SEND_CLAIMED", user.email, send_attempted=True),
            ]
            claimed = OutboundMessageApproval.objects.filter(
                pk=approval.pk,
                status=OutboundMessageApproval.Status.APPROVED,
                send_claimed_at__isnull=True,
            ).update(
                send_attempted=True,
                send_claimed_at=claimed_at,
                line_result_status="SENDING",
                audit_log=claimed_events,
                updated_at=claimed_at,
            )
            if claimed != 1:
                approval.refresh_from_db()
                return approval
            approval.refresh_from_db()

        # The claim above is committed before the external side effect. A crash
        # can leave SENDING for manual reconciliation, but an automatic retry
        # cannot call the provider twice. LINE also receives the UUID retry key.
        try:
            message_id, provider_response = self.provider.push(
                recipient=approval.recipient_ref,
                message=approval.proposed_message,
                token=token,
                retry_key=str(approval.pk),
            )
        except LineUATError as exc:
            return self._record_failure(approval.pk, user=user, error_code=exc.code)

        return self._record_success(
            approval.pk,
            user=user,
            message_id=message_id,
            provider_response=provider_response,
        )

    @transaction.atomic
    def _record_failure(self, approval_id, *, user, error_code):
        approval = self._locked(approval_id)
        if approval.status == OutboundMessageApproval.Status.SENT:
            return approval
        approval.status = OutboundMessageApproval.Status.FAILED
        approval.line_result_status = "FAILED"
        approval.provider_response = {"error_code": error_code}
        approval.audit_log = [
            *_safe_events(approval),
            _audit_event("SEND_FAILED", user.email, send_attempted=True),
        ]
        approval.save(
            update_fields=[
                "status",
                "line_result_status",
                "provider_response",
                "audit_log",
                "updated_at",
            ]
        )
        return approval

    @transaction.atomic
    def _record_success(
        self, approval_id, *, user, message_id, provider_response
    ):
        approval = self._locked(approval_id)
        if approval.status == OutboundMessageApproval.Status.SENT:
            return approval
        approval.status = OutboundMessageApproval.Status.SENT
        approval.sent_at = timezone.now()
        approval.provider_message_id = message_id or None
        approval.provider_response = provider_response
        approval.line_result_status = "SENT"
        approval.audit_log = [
            *_safe_events(approval),
            _audit_event("SENT", user.email, send_attempted=True),
        ]
        approval.save(
            update_fields=[
                "status",
                "sent_at",
                "provider_message_id",
                "provider_response",
                "line_result_status",
                "audit_log",
                "updated_at",
            ]
        )
        return approval

    @staticmethod
    def _locked(approval_id):
        try:
            return OutboundMessageApproval.objects.select_for_update().get(pk=approval_id)
        except (OutboundMessageApproval.DoesNotExist, ValueError) as exc:
            raise LineUATError("not_found", "UAT LINE approval was not found.") from exc

    @staticmethod
    def _validate_uat_invariants(approval):
        if approval.environment != "uat" or approval.synthetic is not True:
            raise LineUATError("uat_boundary_violation", "Only synthetic UAT messages may be sent.")
        if approval.channel != "line":
            raise LineUATError("channel_violation", "Only the LINE UAT channel is allowed.")

    @staticmethod
    def _validate_approved_content(approval):
        expected = approval.approved_content_hash
        actual = _approved_content_hash(approval)
        if not expected or not secrets.compare_digest(expected, actual):
            raise LineUATError(
                "approved_content_changed",
                "Approved message or routing content changed after human review.",
            )

    @staticmethod
    def _validate_recipient(approval):
        allowlisted = _configured_recipient()
        if not allowlisted or approval.recipient_ref != allowlisted:
            raise LineUATError(
                "recipient_not_allowlisted",
                "Recipient does not match LINE_UAT_RECIPIENT_USER_ID.",
            )


def _safe_events(approval):
    return list(approval.audit_log or [])


def serialize_approval(approval):
    """Return the complete non-secret UAT audit contract."""
    return {
        "approval_id": str(approval.pk),
        "rfq_id": approval.rfq_id,
        "environment": approval.environment,
        "synthetic": approval.synthetic,
        "channel": approval.channel,
        "recipient": "UAT allowlisted recipient",
        "proposed_message": approval.proposed_message,
        "final_message": approval.proposed_message,
        "approved_content_hash": approval.approved_content_hash,
        "status": approval.status,
        "ai_payload": approval.ai_payload,
        "approved_by": approval.approved_by.email if approval.approved_by else None,
        "approved_at": approval.approved_at.isoformat() if approval.approved_at else None,
        "rejected_by": approval.rejected_by.email if approval.rejected_by else None,
        "rejected_at": approval.rejected_at.isoformat() if approval.rejected_at else None,
        "sent_at": approval.sent_at.isoformat() if approval.sent_at else None,
        "provider_message_id": approval.provider_message_id,
        "provider_response": approval.provider_response,
        "send_attempted": approval.send_attempted,
        "send_claimed_at": (
            approval.send_claimed_at.isoformat() if approval.send_claimed_at else None
        ),
        "line_result_status": approval.line_result_status,
        "audit_log": approval.audit_log,
        "created_at": approval.created_at.isoformat(),
        "updated_at": approval.updated_at.isoformat(),
        "warning": "UAT / SYNTHETIC — NO REAL CUSTOMER",
    }
