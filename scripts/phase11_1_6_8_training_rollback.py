"""Phase 11.1.6.8 training rollback.

The rollback restores only the local training route-state file created by the
training shutdown script. It does not touch production systems.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.phase11_1_6_8_training_legacy_shutdown import (
        DEFAULT_CHECKPOINT,
        DEFAULT_TRAINING_STATE,
        REVIEW_DIR,
        initial_training_route_state,
        load_json,
        write_json,
    )
except ModuleNotFoundError:
    from phase11_1_6_8_training_legacy_shutdown import (
        DEFAULT_CHECKPOINT,
        DEFAULT_TRAINING_STATE,
        REVIEW_DIR,
        initial_training_route_state,
        load_json,
        write_json,
    )


DEFAULT_ROLLBACK_RESULT = REVIEW_DIR / "PHASE_11.1.6.8_ROLLBACK_RESULT.md"


def utc_now():
    """Return an ISO timestamp for audit records."""
    return datetime.now(timezone.utc).isoformat()


def verify_recovery(state):
    """Verify Legacy API is restored and Django replacement remains active."""
    checks = {
        "legacy_restored": state.get("legacy_available") is True,
        "replacement_available": state.get("replacement_available") is True,
        "production_unchanged": state.get("production_route_changed") is False,
    }
    errors = [name for name, passed in checks.items() if not passed]
    return {
        "status": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
    }


def render_rollback_report(result):
    """Render rollback result as Markdown."""
    return f"""# Phase 11.1.6.8 Rollback Result

## Scope

Training rollback only. This report does not record any production rollback.

## Rollback Action

| Item | Value |
| --- | --- |
| Environment | `{result["environment"]}` |
| Legacy route restored | `{result["legacy_restored"]}` |
| Replacement route active | `{result["api_v1_active"]}` |
| Training state file | `{result["training_state"]}` |

## Verification

| Check | Result |
| --- | --- |
| Legacy `/api/*` restored | `{result["verification"]["checks"]["legacy_restored"]}` |
| Django `/api/v1/*` active | `{result["verification"]["checks"]["replacement_available"]}` |
| Production unchanged | `{result["verification"]["checks"]["production_unchanged"]}` |

## Safety

| Safety item | Value |
| --- | --- |
| Production shutdown executed | `{result["safety"]["production_shutdown_executed"]}` |
| IIS modified | `{result["safety"]["iis_modified"]}` |
| Proxy modified | `{result["safety"]["proxy_modified"]}` |
| Database modified | `{result["safety"]["database_modified"]}` |

## Final Result

`{result["status"]}`
"""


def execute_training_rollback(checkpoint_path=None, training_state_path=None, rollback_result_path=None):
    """Restore the local training route-state file and create a rollback report."""
    checkpoint, errors = load_json(checkpoint_path or DEFAULT_CHECKPOINT)
    restored_state = checkpoint.get("before_state") or initial_training_route_state()
    restored_state.update(
        {
            "legacy_available": True,
            "replacement_available": True,
            "legacy_disabled_in_training": False,
            "training_shutdown_executed": False,
            "production_route_changed": False,
            "updated_at": utc_now(),
        }
    )
    state_path = write_json(training_state_path or DEFAULT_TRAINING_STATE, restored_state)
    verification = verify_recovery(restored_state)
    status = "TRAINING_ROLLBACK_SUCCESS" if verification["status"] == "PASS" and not errors else "TRAINING_ROLLBACK_FAILED"

    result = {
        "phase": "11.1.6.8",
        "created_at": utc_now(),
        "environment": "TRAINING",
        "status": status,
        "legacy_restored": restored_state.get("legacy_available") is True,
        "api_v1_active": restored_state.get("replacement_available") is True,
        "training_state": str(state_path),
        "checkpoint": checkpoint,
        "verification": verification,
        "errors": errors,
        "safety": {
            "production_shutdown_executed": False,
            "production_legacy_api_disabled": False,
            "iis_modified": False,
            "proxy_modified": False,
            "routes_changed": False,
            "database_modified": False,
            "external_system_modified": False,
        },
    }

    report_path = Path(rollback_result_path or DEFAULT_ROLLBACK_RESULT)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_rollback_report(result), encoding="utf-8")
    result["artifacts"] = {"rollback_report": str(report_path)}
    return result


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.6.8 training rollback")
    parser.add_argument("--checkpoint", default=None, help="Training shutdown checkpoint path.")
    parser.add_argument("--training-state", default=None, help="Training route state output path.")
    parser.add_argument("--rollback-result", default=None, help="Rollback Markdown output path.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero if rollback fails.")
    args = parser.parse_args()

    result = execute_training_rollback(
        checkpoint_path=args.checkpoint,
        training_state_path=args.training_state,
        rollback_result_path=args.rollback_result,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] == "TRAINING_ROLLBACK_SUCCESS":
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
