"""Phase 11.1.6 rollback framework for Legacy API decommission.

The rollback script creates a rollback report and tells the operator what must
be restored. It does not edit IIS, proxy rules, Django routes, legacy files or
database state.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXECUTION_DIR = PROJECT_ROOT / "docs" / "migration" / "phase11_1_6_execution"
DEFAULT_REPORT_PATH = DEFAULT_EXECUTION_DIR / "LEGACY_API_DECOMMISSION_ROLLBACK_REPORT.json"


def utc_now():
    """Return an ISO timestamp for audit records."""
    return datetime.now(timezone.utc).isoformat()


def load_checkpoint(path=None):
    """Load the rollback checkpoint created by the execution framework."""
    checkpoint_path = Path(path or DEFAULT_EXECUTION_DIR / "LEGACY_API_DECOMMISSION_ROLLBACK_CHECKPOINT.json")
    if not checkpoint_path.exists():
        return None, f"Rollback checkpoint does not exist: {checkpoint_path}."
    try:
        return json.loads(checkpoint_path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"Rollback checkpoint is invalid JSON: {exc}."


def create_rollback_report(checkpoint_path=None, report_path=None):
    """Create a rollback report from the latest checkpoint."""
    checkpoint, error = load_checkpoint(checkpoint_path)
    errors = []
    if error:
        errors.append(error)

    report = {
        "phase": "11.1.6",
        "created_at": utc_now(),
        "status": "ROLLBACK_READY" if not errors else "ROLLBACK_BLOCKED",
        "rollback_available": not errors,
        "legacy_route": "/api/*",
        "replacement_route": "/api/v1/*",
        "operator_actions": [
            "Restore the previous router/proxy rule for /api/*.",
            "Keep /api/v1/* online.",
            "Run API smoke tests.",
            "Watch error rate, latency and customer impact.",
            "Record final rollback decision.",
        ],
        "script_applies_change": False,
        "legacy_code_deleted": False,
        "database_changed": False,
        "checkpoint": checkpoint,
        "errors": errors,
    }

    output_path = Path(report_path or DEFAULT_REPORT_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report["artifacts"] = {"rollback_report": str(output_path)}
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main():
    """Command line entrypoint for rollback report creation."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.6 rollback framework")
    parser.add_argument("--checkpoint", default=None, help="Rollback checkpoint JSON path.")
    parser.add_argument("--report", default=None, help="Rollback report output path.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when rollback checkpoint is missing. Default exits 0 for local review.",
    )
    args = parser.parse_args()
    result = create_rollback_report(checkpoint_path=args.checkpoint, report_path=args.report)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["rollback_available"]:
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
