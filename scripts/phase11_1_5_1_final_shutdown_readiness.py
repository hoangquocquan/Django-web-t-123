"""Final evidence and approval validator for Phase 11.1.5.1.

This script does not disable routes or change production routing. It only
combines production traffic evidence with final approval data and returns one
decision:

- `READY_FOR_LEGACY_API_SHUTDOWN`
- `KEEP_LEGACY_API_ACTIVE`
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    from scripts.phase11_1_4_production_traffic_evidence import evaluate_traffic_evidence
except ModuleNotFoundError:
    from phase11_1_4_production_traffic_evidence import evaluate_traffic_evidence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROLLBACK_PLAN_PATH = PROJECT_ROOT / "docs" / "migration" / "LEGACY_API_DECOMMISSION_ROLLBACK.md"

TRUTHY_VALUES = {
    "1",
    "true",
    "yes",
    "passed",
    "approved",
    "completed",
    "verified",
    "ready",
}


def truthy(value):
    """Return True only for explicit positive approval values."""
    return str(value or "").strip().lower() in TRUTHY_VALUES


def read_final_approval(env=None):
    """Read final approval details from environment variables."""
    env = env or os.environ
    rollback_plan = Path(env.get("PHASE11_1_5_1_ROLLBACK_PLAN") or ROLLBACK_PLAN_PATH)
    return {
        "technical_approval": truthy(env.get("PHASE11_1_5_1_TECHNICAL_APPROVAL")),
        "technical_name": str(env.get("PHASE11_1_5_1_TECHNICAL_NAME") or "").strip(),
        "technical_role": str(env.get("PHASE11_1_5_1_TECHNICAL_ROLE") or "").strip(),
        "business_approval": truthy(env.get("PHASE11_1_5_1_BUSINESS_APPROVAL")),
        "business_name": str(env.get("PHASE11_1_5_1_BUSINESS_NAME") or "").strip(),
        "business_role": str(env.get("PHASE11_1_5_1_BUSINESS_ROLE") or "").strip(),
        "rollback_ready": truthy(env.get("PHASE11_1_5_1_ROLLBACK_READY")),
        "rollback_owner": str(env.get("PHASE11_1_5_1_ROLLBACK_OWNER") or "").strip(),
        "rollback_contact": str(env.get("PHASE11_1_5_1_ROLLBACK_CONTACT") or "").strip(),
        "monitoring_ready": truthy(env.get("PHASE11_1_5_1_MONITORING_READY")),
        "maintenance_start": str(env.get("PHASE11_1_5_1_MAINTENANCE_START") or "").strip(),
        "maintenance_end": str(env.get("PHASE11_1_5_1_MAINTENANCE_END") or "").strip(),
        "approval_id": str(env.get("PHASE11_1_5_1_APPROVAL_ID") or "").strip(),
        "rollback_plan": rollback_plan,
    }


def validate_traffic(evidence):
    """Validate final production traffic evidence."""
    errors = []
    if not evidence.get("logs_provided"):
        errors.append("Production logs are missing.")
    if evidence.get("legacy_requests") != 0:
        errors.append("Legacy `/api/...` traffic must equal zero.")
    if evidence.get("replacement_requests", 0) <= 0:
        errors.append("Django `/api/v1/...` active usage must be confirmed.")
    if evidence.get("unknown_clients") != 0:
        errors.append("Unknown clients must equal zero.")
    if not evidence.get("safe_to_decommission"):
        errors.append("Traffic evidence is not safe for decommission.")
    return errors


def validate_approval(approval):
    """Validate final technical, business and operations approvals."""
    errors = []
    if not approval["technical_approval"]:
        errors.append("Technical approval is missing.")
    if not approval["technical_name"]:
        errors.append("Technical approver name is missing.")
    if not approval["technical_role"]:
        errors.append("Technical approver role is missing.")
    if not approval["business_approval"]:
        errors.append("Business approval is missing.")
    if not approval["business_name"]:
        errors.append("Business approver name is missing.")
    if not approval["business_role"]:
        errors.append("Business approver role is missing.")
    if not approval["rollback_ready"]:
        errors.append("Rollback readiness is missing.")
    if not approval["rollback_owner"]:
        errors.append("Rollback owner is missing.")
    if not approval["rollback_contact"]:
        errors.append("Rollback contact is missing.")
    if not approval["rollback_plan"].exists():
        errors.append(f"Rollback plan does not exist: {approval['rollback_plan']}.")
    if not approval["monitoring_ready"]:
        errors.append("Monitoring readiness is missing.")
    if not approval["maintenance_start"] or not approval["maintenance_end"]:
        errors.append("Maintenance window start and end are required.")
    if not approval["approval_id"]:
        errors.append("Final approval ID is missing.")
    return errors


def evaluate_final_shutdown_readiness(log_paths=None, period=None, env=None, evidence=None):
    """Return final shutdown readiness based on evidence and approvals."""
    started_at = time.perf_counter()
    env = env or os.environ
    evidence_result = evidence or evaluate_traffic_evidence(log_paths=log_paths, period=period, env=env)
    approval = read_final_approval(env)

    errors = []
    errors.extend(validate_traffic(evidence_result))
    errors.extend(validate_approval(approval))

    ready = not errors
    return {
        "status": "READY_FOR_LEGACY_API_SHUTDOWN" if ready else "KEEP_LEGACY_API_ACTIVE",
        "ready_for_shutdown": ready,
        "legacy_routes_disabled": False,
        "routing_changed": False,
        "proxy_modified": False,
        "database_archived": False,
        "legacy_code_removed": False,
        "evidence": evidence_result,
        "approval": {
            "technical_approval": approval["technical_approval"],
            "technical_name": approval["technical_name"] or None,
            "technical_role": approval["technical_role"] or None,
            "business_approval": approval["business_approval"],
            "business_name": approval["business_name"] or None,
            "business_role": approval["business_role"] or None,
            "rollback_ready": approval["rollback_ready"],
            "rollback_owner": approval["rollback_owner"] or None,
            "rollback_contact": approval["rollback_contact"] or None,
            "rollback_plan": str(approval["rollback_plan"]),
            "monitoring_ready": approval["monitoring_ready"],
            "maintenance_start": approval["maintenance_start"] or None,
            "maintenance_end": approval["maintenance_end"] or None,
            "approval_id": approval["approval_id"] or None,
        },
        "errors": errors,
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
    }


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.5.1 final shutdown readiness validator")
    parser.add_argument("--log", action="append", default=[], help="Production traffic evidence log.")
    parser.add_argument("--period", default=None, help="Verification period label.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when readiness is blocked. Default blocked state exits 0.",
    )
    args = parser.parse_args()
    result = evaluate_final_shutdown_readiness(log_paths=args.log, period=args.period)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["ready_for_shutdown"]:
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
