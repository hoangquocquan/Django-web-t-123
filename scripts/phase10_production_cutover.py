"""Phase 10.5 controlled production cutover execution gate.

This script does not perform destructive actions. It validates whether a human
operator has provided the required production approvals, final backup metadata,
rollback owner and explicit confirmation before manual cutover steps may begin.
"""

from __future__ import annotations

import argparse
import json
import os

try:
    from scripts.phase10_cutover_readiness import evaluate_cutover_readiness
except ImportError:  # pragma: no cover - used when running this file directly.
    from phase10_cutover_readiness import evaluate_cutover_readiness


OPERATOR_CONFIRMATION_ENV = "PHASE10_OPERATOR_CONFIRMATION"
EXPECTED_OPERATOR_CONFIRMATION = "I_UNDERSTAND_PRODUCTION_CUTOVER"
EXECUTION_APPROVAL_ENV = "PHASE10_EXECUTE_CUTOVER_APPROVED"


def confirmation_matches(value):
    """Return True only for the explicit production cutover confirmation phrase."""
    return str(value or "").strip() == EXPECTED_OPERATOR_CONFIRMATION


def approval_enabled(value):
    """Return True when the execution approval flag is explicitly enabled."""
    return str(value or "").strip().lower() in {"1", "true", "yes", "approved"}


def evaluate_cutover_execution(env=None):
    """Evaluate whether manual production cutover execution may proceed."""
    env = env or os.environ
    readiness = evaluate_cutover_readiness(env)
    operator_confirmed = confirmation_matches(env.get(OPERATOR_CONFIRMATION_ENV))
    execution_approved = approval_enabled(env.get(EXECUTION_APPROVAL_ENV))
    errors = list(readiness["errors"])

    if not operator_confirmed:
        errors.append(
            "Missing explicit operator confirmation "
            f"({OPERATOR_CONFIRMATION_ENV}={EXPECTED_OPERATOR_CONFIRMATION})."
        )
    if not execution_approved:
        errors.append(f"Missing execution approval flag ({EXECUTION_APPROVAL_ENV}).")

    allowed = readiness["ready_for_cutover"] and operator_confirmed and execution_approved
    return {
        "status": "ready_for_manual_cutover" if allowed else "blocked_safely",
        "manual_cutover_allowed": allowed,
        "production_cutover_executed": False,
        "destructive_actions_executed": False,
        "database_migration_executed": False,
        "traffic_switched": False,
        "legacy_database_removed": False,
        "readiness": readiness,
        "operator_confirmation": {
            "required_phrase": EXPECTED_OPERATOR_CONFIRMATION,
            "provided": operator_confirmed,
        },
        "execution_approval": {
            "environment_variable": EXECUTION_APPROVAL_ENV,
            "approved": execution_approved,
        },
        "manual_steps": [
            "freeze legacy writes",
            "run final production migration with approved operator",
            "switch production database configuration",
            "run post-cutover validation",
            "enable writes only after validation gates pass",
        ],
        "errors": errors,
    }


def main():
    """CLI entrypoint for Phase 10.5 cutover execution gate."""
    parser = argparse.ArgumentParser(description="Phase 10.5 production cutover gate")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when cutover is blocked. Default exits 0 for safe blocking.",
    )
    args = parser.parse_args()
    result = evaluate_cutover_execution()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["manual_cutover_allowed"]:
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
