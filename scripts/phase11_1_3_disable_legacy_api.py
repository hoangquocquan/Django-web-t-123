"""Controlled disable workflow for Phase 11.1.3.

The workflow does not edit legacy code by default. It creates an auditable
execution decision and a route disable plan. Actual route/proxy changes must be
performed manually after the gate returns `READY_FOR_DECOMMISSION_EXECUTION`.
"""

from __future__ import annotations

import argparse
import json
import sys
import time

try:
    from scripts.phase11_1_2_api_dependency_scanner import REPLACEMENTS
    from scripts.phase11_1_3_api_decommission_gate import evaluate_decommission_gate
except ModuleNotFoundError:
    from phase11_1_2_api_dependency_scanner import REPLACEMENTS
    from phase11_1_3_api_decommission_gate import evaluate_decommission_gate


def build_disable_plan():
    """Build the legacy route disable order without changing application files."""
    return [
        {
            "legacy_route": legacy_route,
            "replacement_route": replacement_route,
            "action": "disable_legacy_proxy_route_after_approval",
            "rollback": "restore_legacy_proxy_route",
        }
        for legacy_route, replacement_route in sorted(REPLACEMENTS.items())
    ]


def run_disable_workflow(log_paths=None, env=None, traffic_result=None):
    """Return the controlled disable decision for this environment."""
    started_at = time.perf_counter()
    gate = evaluate_decommission_gate(log_paths=log_paths, env=env, traffic_result=traffic_result)
    plan = build_disable_plan()

    if not gate["safe_to_execute"]:
        return {
            "status": "BLOCKED_SAFELY",
            "decision": "NO_ROUTE_CHANGE_APPLIED",
            "reason": "Decommission gate did not pass.",
            "legacy_routes_disabled": False,
            "proxy_changes_applied": False,
            "application_code_changed": False,
            "database_changed": False,
            "api_v1_unaffected": True,
            "gate": gate,
            "planned_actions": plan,
            "elapsed_seconds": round(time.perf_counter() - started_at, 4),
        }

    return {
        "status": "READY_FOR_MANUAL_DISABLE",
        "decision": "MANUAL_PROXY_ROUTE_DISABLE_APPROVED",
        "reason": "Gate passed. Apply route changes manually during the approved window.",
        "legacy_routes_disabled": False,
        "proxy_changes_applied": False,
        "application_code_changed": False,
        "database_changed": False,
        "api_v1_unaffected": True,
        "gate": gate,
        "planned_actions": plan,
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
    }


def main():
    """Command line entrypoint for the controlled disable workflow."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.3 controlled legacy API disable workflow")
    parser.add_argument("--log", action="append", default=[], help="Production traffic log path.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when the workflow is blocked. Default keeps blocked state as exit 0.",
    )
    args = parser.parse_args()
    result = run_disable_workflow(log_paths=args.log)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] == "READY_FOR_MANUAL_DISABLE":
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
