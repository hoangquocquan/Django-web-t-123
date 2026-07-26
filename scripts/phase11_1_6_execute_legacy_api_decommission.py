"""Phase 11.1.6 Legacy API decommission execution framework.

The framework creates auditable execution and rollback checkpoint records. It
does not edit source code, Django URL config, IIS config, proxy rules or the
database. In production, a human operator applies the approved route change
after this script returns `READY_TO_EXECUTE`.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.phase11_1_6_pre_shutdown_validation import evaluate_pre_shutdown_validation
except ModuleNotFoundError:
    from phase11_1_6_pre_shutdown_validation import evaluate_pre_shutdown_validation


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "migration" / "phase11_1_6_execution"


def utc_now():
    """Return an ISO timestamp for audit records."""
    return datetime.now(timezone.utc).isoformat()


def record_current_api_state():
    """Record expected route state before production operators change routing."""
    return {
        "legacy_route": "/api/*",
        "legacy_route_expected_available_before_shutdown": True,
        "replacement_route": "/api/v1/*",
        "replacement_route_expected_available": True,
        "source_code_changed": False,
        "database_changed": False,
        "production_proxy_changed_by_script": False,
    }


def build_route_disable_plan():
    """Build route-level instructions without applying them."""
    return {
        "action": "disable_legacy_api_route_in_production_router",
        "legacy_route": "/api/*",
        "keep_active": "/api/v1/*",
        "operator_note": "Apply only during the approved maintenance window after READY_TO_EXECUTE.",
        "script_applies_change": False,
    }


def verify_post_shutdown_state(route_state=None):
    """Validate post-shutdown route state from a caller-provided snapshot."""
    state = route_state or {}
    legacy_unavailable = state.get("legacy_available") is False
    replacement_available = state.get("replacement_available") is True
    errors = []
    if not legacy_unavailable:
        errors.append("Legacy `/api/*` route is still available or was not verified.")
    if not replacement_available:
        errors.append("Replacement `/api/v1/*` route is unavailable or was not verified.")
    return {
        "legacy_route_unavailable": legacy_unavailable,
        "replacement_api_available": replacement_available,
        "valid": legacy_unavailable and replacement_available,
        "errors": errors,
    }


def write_json(path, payload):
    """Write an audit JSON file."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


def execute_legacy_api_decommission(
    evidence_report_path=None,
    env=None,
    output_dir=None,
    route_state=None,
):
    """Create execution records and return the decommission decision."""
    started_at = time.perf_counter()
    output_path = Path(output_dir or DEFAULT_OUTPUT_DIR)
    validation = evaluate_pre_shutdown_validation(evidence_report_path=evidence_report_path, env=env)
    api_state = record_current_api_state()
    rollback_checkpoint = {
        "created_at": utc_now(),
        "rollback_route": "/api/*",
        "replacement_route": "/api/v1/*",
        "restore_action": "restore_previous_router_or_proxy_rule",
        "legacy_code_available": True,
        "database_unchanged": True,
    }

    execution_record = {
        "phase": "11.1.6",
        "created_at": utc_now(),
        "validation_status": validation["status"],
        "api_state_before": api_state,
        "rollback_checkpoint": rollback_checkpoint,
        "route_disable_plan": build_route_disable_plan(),
        "legacy_routes_disabled_by_script": False,
        "api_v1_kept_active": True,
        "source_code_changed": False,
        "database_changed": False,
    }

    if not validation["execution_allowed"]:
        result = {
            "status": "BLOCKED_SAFELY",
            "execution_status": "NOT_EXECUTED",
            "reason": "Pre-shutdown validation did not pass.",
            "validation": validation,
            "execution_record": execution_record,
            "post_shutdown_validation": None,
            "elapsed_seconds": round(time.perf_counter() - started_at, 4),
        }
    else:
        post_shutdown = verify_post_shutdown_state(route_state)
        result = {
            "status": "READY_TO_EXECUTE",
            "execution_status": "AWAITING_APPROVED_PRODUCTION_ROUTE_CHANGE",
            "reason": "Safety gate passed. Production operator must apply route change and provide post-shutdown state.",
            "validation": validation,
            "execution_record": execution_record,
            "post_shutdown_validation": post_shutdown,
            "elapsed_seconds": round(time.perf_counter() - started_at, 4),
        }

    execution_file = write_json(output_path / "LEGACY_API_DECOMMISSION_EXECUTION_RECORD.json", result)
    checkpoint_file = write_json(output_path / "LEGACY_API_DECOMMISSION_ROLLBACK_CHECKPOINT.json", rollback_checkpoint)
    result["artifacts"] = {
        "execution_record": str(execution_file),
        "rollback_checkpoint": str(checkpoint_file),
    }
    write_json(execution_file, result)
    return result


def main():
    """Command line entrypoint for the execution framework."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.6 legacy API decommission execution framework")
    parser.add_argument("--evidence-report", default=None, help="Path to production evidence JSON report.")
    parser.add_argument("--output-dir", default=None, help="Directory for execution audit records.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when execution is blocked. Default blocked state exits 0.",
    )
    args = parser.parse_args()
    result = execute_legacy_api_decommission(evidence_report_path=args.evidence_report, output_dir=args.output_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] == "READY_TO_EXECUTE":
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
