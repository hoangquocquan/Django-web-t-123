"""Phase 10.6 post-production cutover validation workflow.

This script validates post-cutover readiness and delegates production database
checks to the Phase 10.5 post-cutover validator. It does not remove legacy,
delete backups or perform destructive cleanup.
"""

from __future__ import annotations

import argparse
import json
import os
import time

try:
    from scripts.phase10_post_cutover_validation import evaluate_post_cutover_validation
except ImportError:  # pragma: no cover - used when running this file directly.
    from phase10_post_cutover_validation import evaluate_post_cutover_validation


REQUIRED_BUSINESS_FLAGS = {
    "PHASE10_CATALOG_FLOW_VALIDATED": "catalog flow",
    "PHASE10_CRM_FLOW_VALIDATED": "CRM flow",
    "PHASE10_SALES_FLOW_VALIDATED": "sales flow",
    "PHASE10_CMS_FLOW_VALIDATED": "CMS flow",
    "PHASE10_AUTH_FLOW_VALIDATED": "authentication flow",
}
REQUIRED_MONITORING_FLAGS = {
    "PHASE10_ERROR_MONITORING_CLEAN": "error monitoring clean",
    "PHASE10_PERFORMANCE_BASELINE_RECORDED": "performance baseline recorded",
    "PHASE10_ROLLBACK_WINDOW_COMPLETE": "rollback window complete",
    "PHASE10_BUSINESS_APPROVAL_RECEIVED": "business approval received",
}


def flag_enabled(value):
    """Return True when a post-cutover validation flag is explicitly enabled."""
    return str(value or "").strip().lower() in {"1", "true", "yes", "passed", "approved", "completed"}


def evaluate_flags(env, required_flags):
    """Evaluate a group of required environment validation flags."""
    results = {}
    errors = []
    for key, label in required_flags.items():
        passed = flag_enabled(env.get(key))
        results[key] = {
            "label": label,
            "passed": passed,
        }
        if not passed:
            errors.append(f"Missing validation: {label} ({key}).")
    return results, errors


def evaluate_post_production_validation(env=None):
    """Evaluate Phase 10.6 post-production validation status."""
    started_at = time.perf_counter()
    env = env or os.environ
    cutover_validation = evaluate_post_cutover_validation(env)
    business, business_errors = evaluate_flags(env, REQUIRED_BUSINESS_FLAGS)
    monitoring, monitoring_errors = evaluate_flags(env, REQUIRED_MONITORING_FLAGS)
    errors = list(cutover_validation["errors"]) + business_errors + monitoring_errors
    validation_passed = (
        cutover_validation["status"] == "passed"
        and not business_errors
        and not monitoring_errors
    )

    legacy_shutdown_recommendation = (
        "ALLOW_PHASE_11" if validation_passed else "KEEP_LEGACY_ACTIVE"
    )
    status = "passed" if validation_passed else "blocked_safely"
    return {
        "status": status,
        "production_validation_result": status,
        "legacy_shutdown_recommendation": legacy_shutdown_recommendation,
        "destructive_cleanup_executed": False,
        "legacy_shutdown_executed": False,
        "backups_removed": False,
        "rollback_capability_removed": False,
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
        "application": {
            "django_system_check": "run python manage.py check",
            "service_startup": "pending production marker",
            "error_monitoring": monitoring.get("PHASE10_ERROR_MONITORING_CLEAN", {}),
        },
        "database": cutover_validation["database"],
        "api": {
            "health": cutover_validation["application"]["api_health"],
            "response_validation": "pending production marker",
            "performance_check": monitoring.get("PHASE10_PERFORMANCE_BASELINE_RECORDED", {}),
        },
        "business": business,
        "monitoring": monitoring,
        "errors": errors,
    }


def main():
    """CLI entrypoint for Phase 10.6 post-production validation."""
    parser = argparse.ArgumentParser(description="Phase 10.6 post-production validation")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when validation is blocked. Default exits 0 for safe blocking.",
    )
    args = parser.parse_args()
    result = evaluate_post_production_validation()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] == "passed":
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
