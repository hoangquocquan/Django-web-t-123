"""Phase 11.1.6 pre-shutdown validation for Legacy API decommission.

This script is the final safety gate before any `/api/*` shutdown work. It only
reads evidence and approval records. It does not change routes, proxy config,
legacy code, database files or production settings.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE_REPORT = (
    PROJECT_ROOT
    / "docs"
    / "migration"
    / "production_evidence"
    / "reports"
    / "REAL_PRODUCTION_TRAFFIC_REPORT.json"
)
APPROVAL_FILES = {
    "technical_approval": PROJECT_ROOT
    / "docs"
    / "migration"
    / "production_evidence"
    / "approvals"
    / "TECHNICAL_APPROVAL.md",
    "business_approval": PROJECT_ROOT
    / "docs"
    / "migration"
    / "production_evidence"
    / "approvals"
    / "BUSINESS_APPROVAL.md",
    "rollback_owner": PROJECT_ROOT
    / "docs"
    / "migration"
    / "production_evidence"
    / "approvals"
    / "ROLLBACK_OWNER.md",
    "maintenance_window": PROJECT_ROOT
    / "docs"
    / "migration"
    / "production_evidence"
    / "approvals"
    / "MAINTENANCE_WINDOW.md",
    "monitoring_ready": PROJECT_ROOT
    / "docs"
    / "migration"
    / "production_evidence"
    / "monitoring"
    / "MONITORING_READINESS_CONFIRMATION.md",
}

TRUTHY_VALUES = {"1", "true", "yes", "approved", "complete", "completed", "ready", "verified"}
PENDING_VALUES = {"pending", "not_provided", "missing", "tbd", ""}


def truthy(value):
    """Return True only for explicit positive values."""
    return str(value or "").strip().lower() in TRUTHY_VALUES


def has_pending_marker(text):
    """Detect whether an approval document still contains placeholder values."""
    lowered = str(text or "").lower()
    return any(marker in lowered for marker in PENDING_VALUES if marker)


def document_looks_approved(path):
    """Validate a human approval document without trusting blank templates."""
    document_path = Path(path)
    if not document_path.exists():
        return False, f"Approval document does not exist: {document_path}."

    content = document_path.read_text(encoding="utf-8", errors="ignore")
    if has_pending_marker(content):
        return False, f"Approval document still contains pending markers: {document_path}."
    if not any(token in content.lower() for token in TRUTHY_VALUES):
        return False, f"Approval document has no explicit approval marker: {document_path}."
    return True, None


def load_evidence_report(path=None):
    """Load production evidence JSON report."""
    report_path = Path(path or DEFAULT_EVIDENCE_REPORT)
    if not report_path.exists():
        return {
            "status": "INCOMPLETE_EVIDENCE_PACKAGE",
            "ready_for_shutdown": False,
            "errors": [f"Evidence report does not exist: {report_path}."],
        }

    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "status": "INCOMPLETE_EVIDENCE_PACKAGE",
            "ready_for_shutdown": False,
            "errors": [f"Evidence report is invalid JSON: {exc}."],
        }


def validate_evidence(evidence):
    """Validate complete production evidence before shutdown execution."""
    errors = []
    if evidence.get("status") != "COMPLETE_EVIDENCE_PACKAGE":
        errors.append("Production evidence is not COMPLETE_EVIDENCE_PACKAGE.")
    if not evidence.get("ready_for_shutdown"):
        errors.append("Production evidence is not marked ready_for_shutdown.")
    if evidence.get("legacy_requests") != 0:
        errors.append("Legacy `/api/*` traffic must be zero.")
    if evidence.get("django_requests", 0) <= 0:
        errors.append("Replacement `/api/v1/*` traffic must be observed.")
    if evidence.get("unknown_clients") != 0:
        errors.append("Unknown clients must be zero.")
    if evidence.get("routes_changed") or evidence.get("proxy_modified"):
        errors.append("Evidence package indicates routes/proxy were already changed.")
    return errors


def read_approval_context(env=None, approval_files=None):
    """Read approvals from environment overrides or approval documents."""
    env = env or os.environ
    approval_files = approval_files or APPROVAL_FILES
    result = {}
    errors = []

    env_map = {
        "technical_approval": "PHASE11_1_6_TECHNICAL_APPROVAL",
        "business_approval": "PHASE11_1_6_BUSINESS_APPROVAL",
        "rollback_owner": "PHASE11_1_6_ROLLBACK_OWNER",
        "maintenance_window": "PHASE11_1_6_MAINTENANCE_WINDOW",
        "monitoring_ready": "PHASE11_1_6_MONITORING_READY",
    }

    for key, env_name in env_map.items():
        env_value = str(env.get(env_name) or "").strip()
        if env_value:
            approved = truthy(env_value) or (key == "rollback_owner" and env_value.lower() not in PENDING_VALUES)
            result[key] = approved
            if not approved:
                errors.append(f"{key} is not approved by {env_name}.")
            continue

        approved, error = document_looks_approved(approval_files[key])
        result[key] = approved
        if error:
            errors.append(error)

    return result, errors


def evaluate_pre_shutdown_validation(evidence_report_path=None, env=None, evidence=None, approval_files=None):
    """Return `READY_TO_EXECUTE` or `BLOCKED_SAFELY`."""
    started_at = time.perf_counter()
    evidence_result = evidence or load_evidence_report(evidence_report_path)
    approval_result, approval_errors = read_approval_context(env=env, approval_files=approval_files)

    errors = []
    errors.extend(evidence_result.get("errors", []))
    errors.extend(validate_evidence(evidence_result))
    errors.extend(approval_errors)

    ready = not errors
    return {
        "status": "READY_TO_EXECUTE" if ready else "BLOCKED_SAFELY",
        "execution_allowed": ready,
        "evidence_status": evidence_result.get("status", "UNKNOWN"),
        "approval_status": "APPROVED" if all(approval_result.values()) else "PENDING_OR_INCOMPLETE",
        "evidence": {
            "ready_for_shutdown": bool(evidence_result.get("ready_for_shutdown")),
            "legacy_requests": evidence_result.get("legacy_requests"),
            "django_requests": evidence_result.get("django_requests"),
            "unknown_clients": evidence_result.get("unknown_clients"),
        },
        "approval": approval_result,
        "errors": errors,
        "safety": {
            "legacy_code_deleted": False,
            "database_deleted": False,
            "database_archived": False,
            "migrations_removed": False,
            "approval_gate_bypassed": False,
        },
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
    }


def main():
    """Command line entrypoint for the Phase 11.1.6 safety gate."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.6 pre-shutdown validation")
    parser.add_argument("--evidence-report", default=None, help="Path to production evidence JSON report.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when shutdown is blocked. Default blocked state exits 0.",
    )
    args = parser.parse_args()
    result = evaluate_pre_shutdown_validation(evidence_report_path=args.evidence_report)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["execution_allowed"]:
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
