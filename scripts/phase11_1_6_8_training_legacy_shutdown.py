"""Phase 11.1.6.8 training Legacy API shutdown execution.

This script only changes a local training state file. It does not edit IIS,
proxy rules, Django routes, legacy backend files, or database state.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXECUTION_DIR = PROJECT_ROOT / "docs" / "migration" / "phase11_1_6_execution"
REVIEW_DIR = PROJECT_ROOT / "docs" / "reviews"

DEFAULT_TRAINING_STATUS = EXECUTION_DIR / "FINAL_READINESS_SIMULATION_STATUS.json"
DEFAULT_PRODUCTION_STATUS = EXECUTION_DIR / "FINAL_READINESS_STATUS.json"
DEFAULT_TRAINING_STATE = EXECUTION_DIR / "TRAINING_LEGACY_API_ROUTE_STATE.json"
DEFAULT_CHECKPOINT = EXECUTION_DIR / "TRAINING_LEGACY_API_SHUTDOWN_CHECKPOINT.json"
DEFAULT_SHUTDOWN_RESULT = REVIEW_DIR / "PHASE_11.1.6.8_SHUTDOWN_RESULT.json"
DEFAULT_TRAFFIC_VERIFICATION = REVIEW_DIR / "PHASE_11.1.6.8_TRAFFIC_VERIFICATION.md"
DEFAULT_EXECUTION_REPORT = REVIEW_DIR / "PHASE_11.1.6.8_TRAINING_SHUTDOWN_REPORT.md"


def utc_now():
    """Return an ISO timestamp for audit records."""
    return datetime.now(timezone.utc).isoformat()


def load_json(path):
    """Load JSON and return a tuple of payload and validation errors."""
    json_path = Path(path)
    if not json_path.exists():
        return {}, [f"JSON file does not exist: {json_path}."]
    try:
        return json.loads(json_path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return {}, [f"JSON file is invalid: {json_path}: {exc}."]


def write_json(path, payload):
    """Write JSON with stable UTF-8 formatting."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


def initial_training_route_state():
    """Return the expected route state before the training shutdown."""
    return {
        "environment": "TRAINING",
        "legacy_route": "/api/*",
        "legacy_available": True,
        "replacement_route": "/api/v1/*",
        "replacement_available": True,
        "legacy_disabled_in_training": False,
        "production_route_changed": False,
        "iis_modified": False,
        "proxy_modified": False,
        "database_modified": False,
        "updated_at": utc_now(),
    }


def disabled_training_route_state():
    """Return the expected route state after the training shutdown."""
    state = initial_training_route_state()
    state.update(
        {
            "legacy_available": False,
            "legacy_disabled_in_training": True,
            "training_shutdown_executed": True,
            "updated_at": utc_now(),
        }
    )
    return state


def validate_training_only(training_status_path=None, production_status_path=None):
    """Verify training can run and production is still blocked safely."""
    training_status, training_errors = load_json(training_status_path or DEFAULT_TRAINING_STATUS)
    production_status, production_errors = load_json(production_status_path or DEFAULT_PRODUCTION_STATUS)
    errors = list(training_errors) + list(production_errors)

    training_evidence = training_status.get("gates", {}).get("evidence", {})
    production_safety = production_status.get("safety", {})

    if training_status.get("decision") != "READY_TO_EXECUTE_TRAINING":
        errors.append("Training readiness decision is not READY_TO_EXECUTE_TRAINING.")
    if training_evidence.get("evidence_status") != "TRAINING_ONLY":
        errors.append("Training evidence status is not TRAINING_ONLY.")
    if training_evidence.get("simulation") is not True:
        errors.append("Training evidence is not marked as simulation.")
    if production_status.get("decision") != "BLOCKED_SAFELY":
        errors.append("Production readiness is not BLOCKED_SAFELY.")
    if production_safety.get("shutdown_executed") is not False:
        errors.append("Production status indicates shutdown execution.")
    if production_safety.get("legacy_api_disabled") is not False:
        errors.append("Production status indicates Legacy API disabled.")

    return {
        "status": "PASS" if not errors else "FAIL",
        "training_decision": training_status.get("decision", "UNKNOWN"),
        "training_evidence_status": training_evidence.get("evidence_status", "UNKNOWN"),
        "production_decision": production_status.get("decision", "UNKNOWN"),
        "production_safety": production_safety,
        "errors": errors,
    }


def create_pre_shutdown_checkpoint(path=None):
    """Create a checkpoint that rollback can use to restore training state."""
    checkpoint = {
        "phase": "11.1.6.8",
        "created_at": utc_now(),
        "environment": "TRAINING",
        "before_state": initial_training_route_state(),
        "restore_action": "restore_training_legacy_api_route_state",
        "production_shutdown_allowed": False,
        "production_shutdown_executed": False,
    }
    output_path = write_json(path or DEFAULT_CHECKPOINT, checkpoint)
    checkpoint["artifact"] = str(output_path)
    write_json(output_path, checkpoint)
    return checkpoint


def verify_training_route_state(before_state, after_state):
    """Compare before and after route state for the training shutdown."""
    checks = {
        "before_legacy_available": before_state.get("legacy_available") is True,
        "before_replacement_available": before_state.get("replacement_available") is True,
        "after_legacy_disabled": after_state.get("legacy_available") is False,
        "after_replacement_available": after_state.get("replacement_available") is True,
        "production_unchanged": after_state.get("production_route_changed") is False,
    }
    errors = [name for name, passed in checks.items() if not passed]
    return {
        "status": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
    }


def render_traffic_verification(result):
    """Render the before/after traffic verification as Markdown."""
    before = result["before_state"]
    after = result["after_state"]
    verification = result["traffic_verification"]
    return f"""# Phase 11.1.6.8 Traffic Verification

## Scope

Training environment only. This file verifies a local training route-state
simulation and does not prove production shutdown readiness.

## Before

| Route | Expected state | Observed |
| --- | --- | --- |
| `/api/*` | AVAILABLE | `{"AVAILABLE" if before["legacy_available"] else "DISABLED"}` |
| `/api/v1/*` | AVAILABLE | `{"AVAILABLE" if before["replacement_available"] else "DISABLED"}` |

## After

| Route | Expected state | Observed |
| --- | --- | --- |
| `/api/*` | DISABLED | `{"AVAILABLE" if after["legacy_available"] else "DISABLED"}` |
| `/api/v1/*` | AVAILABLE | `{"AVAILABLE" if after["replacement_available"] else "DISABLED"}` |

## Safety

| Item | Value |
| --- | --- |
| Production route changed | `{after["production_route_changed"]}` |
| IIS modified | `{after["iis_modified"]}` |
| Proxy modified | `{after["proxy_modified"]}` |
| Database modified | `{after["database_modified"]}` |

## Result

`{verification["status"]}`
"""


def render_execution_report(result):
    """Render a human-readable training shutdown execution report."""
    return f"""# Phase 11.1.6.8 Training Shutdown Report

## Objective

Practice Legacy API shutdown in training while keeping production blocked.

## Pre-Check

| Check | Result |
| --- | --- |
| Training readiness | `{result["precheck"]["training_decision"]}` |
| Evidence status | `{result["precheck"]["training_evidence_status"]}` |
| Production readiness | `{result["precheck"]["production_decision"]}` |
| Pre-check result | `{result["precheck"]["status"]}` |

## Shutdown Action

| Item | Value |
| --- | --- |
| Environment | `{result["environment"]}` |
| Legacy route | `{result["legacy_route"]}` |
| Legacy route disabled in training | `{result["training_legacy_disabled"]}` |
| Replacement route | `{result["replacement_route"]}` |
| Replacement route active | `{result["api_v1_active"]}` |

## Verification

Traffic verification result:

`{result["traffic_verification"]["status"]}`

## Safety Confirmation

| Safety item | Value |
| --- | --- |
| Production shutdown executed | `{result["safety"]["production_shutdown_executed"]}` |
| Real IIS modified | `{result["safety"]["iis_modified"]}` |
| Real proxy modified | `{result["safety"]["proxy_modified"]}` |
| Real routes changed | `{result["safety"]["routes_changed"]}` |
| Database modified | `{result["safety"]["database_modified"]}` |

## Final Result

`{result["status"]}`

## Rollback

Run:

```powershell
python scripts\\phase11_1_6_8_training_rollback.py
```
"""


def execute_training_shutdown(
    training_status_path=None,
    production_status_path=None,
    training_state_path=None,
    checkpoint_path=None,
    shutdown_result_path=None,
    traffic_verification_path=None,
    execution_report_path=None,
):
    """Execute the training-only Legacy API shutdown simulation."""
    started_at = time.perf_counter()
    precheck = validate_training_only(training_status_path, production_status_path)
    checkpoint = create_pre_shutdown_checkpoint(checkpoint_path)
    before_state = checkpoint["before_state"]

    if precheck["status"] != "PASS":
        after_state = before_state.copy()
        status = "TRAINING_SHUTDOWN_FAILED"
        traffic_verification = verify_training_route_state(before_state, after_state)
    else:
        after_state = disabled_training_route_state()
        write_json(training_state_path or DEFAULT_TRAINING_STATE, after_state)
        status = "TRAINING_SHUTDOWN_SUCCESS"
        traffic_verification = verify_training_route_state(before_state, after_state)

    result = {
        "phase": "11.1.6.8",
        "created_at": utc_now(),
        "environment": "TRAINING",
        "status": status if traffic_verification["status"] == "PASS" else "TRAINING_SHUTDOWN_FAILED",
        "precheck": precheck,
        "legacy_route": "/api/*",
        "replacement_route": "/api/v1/*",
        "training_legacy_disabled": after_state.get("legacy_available") is False,
        "api_v1_active": after_state.get("replacement_available") is True,
        "before_state": before_state,
        "after_state": after_state,
        "traffic_verification": traffic_verification,
        "checkpoint": checkpoint,
        "safety": {
            "production_shutdown_executed": False,
            "production_legacy_api_disabled": False,
            "iis_modified": False,
            "proxy_modified": False,
            "routes_changed": False,
            "database_modified": False,
            "external_system_modified": False,
        },
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
    }

    shutdown_path = write_json(shutdown_result_path or DEFAULT_SHUTDOWN_RESULT, result)
    traffic_path = Path(traffic_verification_path or DEFAULT_TRAFFIC_VERIFICATION)
    traffic_path.parent.mkdir(parents=True, exist_ok=True)
    traffic_path.write_text(render_traffic_verification(result), encoding="utf-8")
    report_path = Path(execution_report_path or DEFAULT_EXECUTION_REPORT)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_execution_report(result), encoding="utf-8")

    result["artifacts"] = {
        "shutdown_result": str(shutdown_path),
        "traffic_verification": str(traffic_path),
        "execution_report": str(report_path),
        "training_state": str(Path(training_state_path or DEFAULT_TRAINING_STATE)),
    }
    write_json(shutdown_path, result)
    return result


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.6.8 training Legacy API shutdown")
    parser.add_argument("--training-status", default=None, help="Training readiness JSON path.")
    parser.add_argument("--production-status", default=None, help="Production readiness JSON path.")
    parser.add_argument("--training-state", default=None, help="Training route state output path.")
    parser.add_argument("--checkpoint", default=None, help="Checkpoint output path.")
    parser.add_argument("--shutdown-result", default=None, help="Shutdown result JSON path.")
    parser.add_argument("--traffic-verification", default=None, help="Traffic verification Markdown path.")
    parser.add_argument("--execution-report", default=None, help="Execution report Markdown path.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero if training shutdown fails.")
    args = parser.parse_args()

    result = execute_training_shutdown(
        training_status_path=args.training_status,
        production_status_path=args.production_status,
        training_state_path=args.training_state,
        checkpoint_path=args.checkpoint,
        shutdown_result_path=args.shutdown_result,
        traffic_verification_path=args.traffic_verification,
        execution_report_path=args.execution_report,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] == "TRAINING_SHUTDOWN_SUCCESS":
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
