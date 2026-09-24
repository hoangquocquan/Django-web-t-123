"""Local n8n automation helpers for Business + AI Wave 2.

File nay khong ket noi n8n that theo mac dinh. No mo phong va validate workflow
local de nguoi hoc thay duoc luong automation ma van giu an toan: khong deploy,
khong gui email that, khong bo qua human approval.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
N8N_DIR = PROJECT_ROOT / "n8n"
RESULT_PATH = N8N_DIR / "results" / "business_wave2_execution.json"
DEFAULT_SECRET = "local-business-wave-2-secret"


def utc_now():
    """Tra ve thoi gian UTC de report co dau vet."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sign_payload(payload, secret=DEFAULT_SECRET):
    """Tao chu ky HMAC cho webhook payload local."""
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()


def validate_webhook_signature(payload, signature, secret=DEFAULT_SECRET):
    """Kiem tra webhook co dung secret khong."""
    expected = sign_payload(payload, secret=secret)
    return hmac.compare_digest(expected, str(signature or ""))


def website_lead_workflow(payload):
    """Mo phong luong Website Lead -> CRM -> AI Lead Analysis -> Notification."""
    return {
        "workflow": "website_lead_to_sales_notification",
        "steps": [
            {"name": "Website Lead", "status": "RECEIVED"},
            {"name": "Django CRM", "status": "READY_TO_CREATE_RECORD"},
            {"name": "AI Lead Analysis", "status": "SUGGESTION_ONLY"},
            {"name": "Sales Notification", "status": "DRAFT_NOTIFICATION"},
        ],
        "lead": payload,
        "human_approval_required": True,
    }


def document_update_workflow(payload):
    """Mo phong luong New Document -> OCR -> Knowledge Update."""
    return {
        "workflow": "document_to_knowledge_update",
        "steps": [
            {"name": "New Document", "status": "RECEIVED"},
            {"name": "OCR/Text Extraction", "status": "LOCAL_EXTRACTION"},
            {"name": "Knowledge Update", "status": "PENDING_HUMAN_REVIEW"},
        ],
        "document": payload,
        "human_approval_required": True,
    }


def follow_up_workflow(payload):
    """Mo phong luong Sales Follow-up -> Reminder -> Notification."""
    return {
        "workflow": "sales_follow_up_reminder",
        "steps": [
            {"name": "Sales Follow-up", "status": "SCHEDULED"},
            {"name": "Reminder", "status": "LOCAL_ONLY"},
            {"name": "Notification", "status": "DRAFT_NOTIFICATION"},
        ],
        "follow_up": payload,
        "human_approval_required": True,
    }


def run_local_automation(workflow_name, payload, signature=None, secret=DEFAULT_SECRET, output_path=RESULT_PATH):
    """Chay mot workflow local va ghi ket qua ra file evidence."""
    if signature is not None and not validate_webhook_signature(payload, signature, secret=secret):
        result = {
            "status": "BLOCKED",
            "reason": "Invalid webhook signature.",
            "workflow": workflow_name,
            "created_at": utc_now(),
        }
    else:
        handlers = {
            "website_lead": website_lead_workflow,
            "document_update": document_update_workflow,
            "sales_follow_up": follow_up_workflow,
        }
        handler = handlers.get(workflow_name)
        if not handler:
            result = {"status": "BLOCKED", "reason": "Unknown workflow.", "workflow": workflow_name}
        else:
            result = {
                "status": "N8N_LOCAL_AUTOMATION_READY",
                "created_at": utc_now(),
                "result": handler(payload),
                "safety": {
                    "local_only": True,
                    "production_deployed": False,
                    "external_email_sent": False,
                    "human_approval_required": True,
                },
            }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main():
    """Entrypoint demo nhanh cho workflow lead."""
    payload = {"company": "Demo CNC Buyer", "need": "CNC shaft quotation"}
    result = run_local_automation("website_lead", payload, sign_payload(payload))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

