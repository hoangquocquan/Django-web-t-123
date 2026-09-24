"""Validate final readiness before legacy API shutdown.

This phase does not disable routes. It only combines compatibility, traffic,
rollback and approval evidence into a final decision:

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
COMPATIBILITY_MATRIX_PATH = PROJECT_ROOT / "docs" / "migration" / "LEGACY_API_COMPATIBILITY_MATRIX.md"
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
    """Convert explicit environment values to boolean readiness flags."""
    return str(value or "").strip().lower() in TRUTHY_VALUES


def read_compatibility_status(path=None):
    """Read the compatibility matrix and determine whether replacements are ready."""
    matrix_path = Path(path or COMPATIBILITY_MATRIX_PATH)
    if not matrix_path.exists():
        return {
            "replacement_ready": False,
            "ready_replacements": 0,
            "not_ready_replacements": None,
            "errors": [f"Compatibility matrix not found: {matrix_path}."],
        }

    content = matrix_path.read_text(encoding="utf-8", errors="ignore")
    ready_count = content.count("| READY |")
    not_ready_is_zero = "Not ready replacements: 0" in content
    replacement_ready = ready_count > 0 and not_ready_is_zero
    return {
        "replacement_ready": replacement_ready,
        "ready_replacements": ready_count,
        "not_ready_replacements": 0 if not_ready_is_zero else "unknown",
        "errors": [] if replacement_ready else ["API compatibility is not fully ready."],
    }


def read_approval_context(env=None):
    """Read technical, business and operational approval flags."""
    env = env or os.environ
    rollback_plan = Path(env.get("PHASE11_1_5_ROLLBACK_PLAN") or ROLLBACK_PLAN_PATH)
    return {
        "technical_approved": truthy(env.get("PHASE11_1_5_TECHNICAL_APPROVED")),
        "business_approved": truthy(env.get("PHASE11_1_5_BUSINESS_APPROVED")),
        "rollback_ready": truthy(env.get("PHASE11_1_5_ROLLBACK_READY")),
        "rollback_owner": str(env.get("PHASE11_1_5_ROLLBACK_OWNER") or "").strip(),
        "maintenance_window_approved": truthy(env.get("PHASE11_1_5_MAINTENANCE_WINDOW_APPROVED")),
        "monitoring_ready": truthy(env.get("PHASE11_1_5_MONITORING_READY")),
        "support_notified": truthy(env.get("PHASE11_1_5_SUPPORT_NOTIFIED")),
        "user_impact_reviewed": truthy(env.get("PHASE11_1_5_USER_IMPACT_REVIEWED")),
        "approval_id": str(env.get("PHASE11_1_5_APPROVAL_ID") or "").strip(),
        "rollback_plan": rollback_plan,
    }


def validate_approval_context(context):
    """Return approval errors that block shutdown."""
    errors = []
    if not context["technical_approved"]:
        errors.append("Technical approval is missing.")
    if not context["business_approved"]:
        errors.append("Business approval is missing.")
    if not context["rollback_ready"]:
        errors.append("Rollback readiness is missing.")
    if not context["rollback_owner"]:
        errors.append("Rollback owner is missing.")
    if not context["rollback_plan"].exists():
        errors.append(f"Rollback plan does not exist: {context['rollback_plan']}.")
    if not context["maintenance_window_approved"]:
        errors.append("Maintenance window approval is missing.")
    if not context["monitoring_ready"]:
        errors.append("Monitoring readiness is missing.")
    if not context["support_notified"]:
        errors.append("Support team notification is missing.")
    if not context["user_impact_reviewed"]:
        errors.append("User impact review is missing.")
    if not context["approval_id"]:
        errors.append("Final approval ID is missing.")
    return errors


def validate_traffic_evidence(evidence):
    """Return traffic evidence errors that block shutdown."""
    errors = []
    if evidence.get("legacy_requests") != 0:
        errors.append("Legacy API traffic must be zero.")
    if evidence.get("replacement_requests", 0) <= 0:
        errors.append("Django `/api/v1/...` traffic must be active.")
    if evidence.get("unknown_clients") != 0:
        errors.append("Unknown clients must be zero.")
    if evidence.get("status") != "READY_FOR_DECOMMISSION":
        errors.append("Production traffic evidence is not ready for decommission.")
    if not evidence.get("safe_to_decommission"):
        errors.append("Traffic evidence does not allow decommission.")
    return errors


def evaluate_shutdown_readiness(log_paths=None, period=None, env=None, evidence=None, compatibility=None):
    """Evaluate final readiness for legacy API shutdown."""
    started_at = time.perf_counter()
    env = env or os.environ
    evidence_result = evidence or evaluate_traffic_evidence(log_paths=log_paths, period=period, env=env)
    compatibility_result = compatibility or read_compatibility_status()
    approval_context = read_approval_context(env)

    errors = []
    errors.extend(compatibility_result.get("errors", []))
    errors.extend(validate_traffic_evidence(evidence_result))
    errors.extend(validate_approval_context(approval_context))

    ready = not errors
    return {
        "status": "READY_FOR_LEGACY_API_SHUTDOWN" if ready else "KEEP_LEGACY_API_ACTIVE",
        "ready_for_shutdown": ready,
        "legacy_routes_disabled": False,
        "production_routing_changed": False,
        "legacy_code_deleted": False,
        "database_archived": False,
        "rollback_capability_removed": False,
        "compatibility": compatibility_result,
        "evidence": evidence_result,
        "approval": {
            "technical_approved": approval_context["technical_approved"],
            "business_approved": approval_context["business_approved"],
            "rollback_ready": approval_context["rollback_ready"],
            "rollback_owner": approval_context["rollback_owner"] or None,
            "maintenance_window_approved": approval_context["maintenance_window_approved"],
            "monitoring_ready": approval_context["monitoring_ready"],
            "support_notified": approval_context["support_notified"],
            "user_impact_reviewed": approval_context["user_impact_reviewed"],
            "approval_id": approval_context["approval_id"] or None,
            "rollback_plan": str(approval_context["rollback_plan"]),
        },
        "errors": errors,
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
    }


def main():
    """Command line entrypoint for final shutdown readiness approval."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.5 legacy API shutdown readiness check")
    parser.add_argument("--log", action="append", default=[], help="Production traffic evidence log.")
    parser.add_argument("--period", default=None, help="Verification period label.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when readiness is blocked. Default blocked state exits 0.",
    )
    args = parser.parse_args()
    result = evaluate_shutdown_readiness(log_paths=args.log, period=args.period)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["ready_for_shutdown"]:
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
