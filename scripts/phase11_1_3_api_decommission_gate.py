"""Phase 11.1.3 gate for controlled legacy API decommission.

This script is intentionally conservative. It verifies production evidence and
operator approval before any legacy `/api/...` route can be disabled. In the
local/demo environment it should normally return `BLOCKED_SAFELY`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    from scripts.phase11_1_2_legacy_api_traffic_verification import evaluate_traffic
except ModuleNotFoundError:
    from phase11_1_2_legacy_api_traffic_verification import evaluate_traffic


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROLLBACK_PLAN_PATH = PROJECT_ROOT / "docs" / "migration" / "LEGACY_API_DECOMMISSION_ROLLBACK.md"
APPROVAL_CONFIRMATION_TEXT = "I_UNDERSTAND_LEGACY_API_DECOMMISSION_RISK"

TRUTHY_VALUES = {
    "1",
    "true",
    "yes",
    "passed",
    "approved",
    "completed",
    "verified",
}


def truthy(value):
    """Convert explicit operator flags to boolean values."""
    return str(value or "").strip().lower() in TRUTHY_VALUES


def read_operator_context(env=None):
    """Read approval and rollback evidence from environment variables."""
    env = env or os.environ
    rollback_plan = Path(env.get("PHASE11_1_3_ROLLBACK_PLAN") or ROLLBACK_PLAN_PATH)
    return {
        "approval_status": str(env.get("PHASE11_1_3_APPROVAL") or "").strip(),
        "approval_id": str(env.get("PHASE11_1_3_APPROVAL_ID") or "").strip(),
        "operator_confirmation": str(env.get("PHASE11_1_3_OPERATOR_CONFIRMATION") or "").strip(),
        "rollback_ready": truthy(env.get("PHASE11_1_3_ROLLBACK_READY")),
        "rollback_owner": str(env.get("PHASE11_1_3_ROLLBACK_OWNER") or "").strip(),
        "rollback_plan": rollback_plan,
    }


def validate_operator_context(context):
    """Return missing approval/rollback conditions before route disable."""
    errors = []
    checks = {
        "approval_status": context["approval_status"].lower() == "approved",
        "approval_id": bool(context["approval_id"]),
        "operator_confirmation": context["operator_confirmation"] == APPROVAL_CONFIRMATION_TEXT,
        "rollback_ready": context["rollback_ready"],
        "rollback_owner": bool(context["rollback_owner"]),
        "rollback_plan_exists": context["rollback_plan"].exists(),
    }

    if not checks["approval_status"]:
        errors.append("Missing approval: PHASE11_1_3_APPROVAL must be approved.")
    if not checks["approval_id"]:
        errors.append("Missing approval id: PHASE11_1_3_APPROVAL_ID is required.")
    if not checks["operator_confirmation"]:
        errors.append(
            "Missing explicit confirmation: PHASE11_1_3_OPERATOR_CONFIRMATION must match "
            f"{APPROVAL_CONFIRMATION_TEXT}."
        )
    if not checks["rollback_ready"]:
        errors.append("Missing rollback readiness: PHASE11_1_3_ROLLBACK_READY must be approved.")
    if not checks["rollback_owner"]:
        errors.append("Missing rollback owner: PHASE11_1_3_ROLLBACK_OWNER is required.")
    if not checks["rollback_plan_exists"]:
        errors.append(f"Rollback plan file does not exist: {context['rollback_plan']}.")

    return checks, errors


def evaluate_decommission_gate(log_paths=None, env=None, traffic_result=None):
    """Evaluate whether legacy API decommission can proceed."""
    started_at = time.perf_counter()
    context = read_operator_context(env)
    approval_checks, approval_errors = validate_operator_context(context)
    traffic = traffic_result if traffic_result is not None else evaluate_traffic(log_paths, env=env)

    errors = []
    errors.extend(approval_errors)
    if not traffic.get("safe_to_decommission"):
        errors.append("Production traffic evidence does not prove zero legacy API usage.")
    if traffic.get("legacy_requests"):
        errors.append("Legacy API traffic is still present.")
    if traffic.get("unknown_clients"):
        errors.append("Unknown legacy API clients are still present.")

    ready = not errors
    return {
        "status": "READY_FOR_DECOMMISSION_EXECUTION" if ready else "BLOCKED_SAFELY",
        "decision": "ALLOW_CONTROLLED_DISABLE" if ready else "KEEP_LEGACY_API_ACTIVE",
        "safe_to_execute": ready,
        "legacy_routes_disabled": False,
        "legacy_routes_removed": False,
        "compatibility_layer_removed": False,
        "database_changed": False,
        "destructive_actions_executed": False,
        "api_v1_unaffected": True,
        "approval": {
            "checks": approval_checks,
            "approval_id": context["approval_id"] or None,
            "rollback_owner": context["rollback_owner"] or None,
            "rollback_plan": str(context["rollback_plan"]),
        },
        "traffic": traffic,
        "errors": errors,
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
    }


def main():
    """Command line entrypoint for the decommission gate."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.3 legacy API decommission gate")
    parser.add_argument("--log", action="append", default=[], help="Production traffic log path.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when the gate is blocked. Default keeps blocked state as exit 0.",
    )
    args = parser.parse_args()
    result = evaluate_decommission_gate(log_paths=args.log)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["safe_to_execute"]:
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
