"""Final production evidence validator for Phase 11.1.6.1.

The validator reads production evidence and decides whether traffic evidence is
strong enough to unlock Legacy API shutdown execution. It does not disable
routes, edit IIS, change databases or execute shutdown.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE_REPORT = (
    PROJECT_ROOT
    / "docs"
    / "migration"
    / "production_evidence"
    / "reports"
    / "REAL_PRODUCTION_TRAFFIC_REPORT.json"
)


def load_evidence(path=None):
    """Load the production evidence JSON file."""
    evidence_path = Path(path or DEFAULT_EVIDENCE_REPORT)
    if not evidence_path.exists():
        return {
            "status": "INCOMPLETE_EVIDENCE_PACKAGE",
            "ready_for_shutdown": False,
            "errors": [f"Evidence report does not exist: {evidence_path}."],
        }

    try:
        return json.loads(evidence_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "status": "INCOMPLETE_EVIDENCE_PACKAGE",
            "ready_for_shutdown": False,
            "errors": [f"Evidence report is invalid JSON: {exc}."],
        }


def replacement_request_count(evidence):
    """Read Django replacement API request count from supported report keys."""
    return int(evidence.get("django_requests") or evidence.get("replacement_requests") or 0)


def validate_final_evidence(evidence):
    """Return blocking errors for final production traffic evidence."""
    errors = []
    legacy_requests = int(evidence.get("legacy_requests") or 0)
    replacement_requests = replacement_request_count(evidence)
    unknown_clients = int(evidence.get("unknown_clients") or 0)

    if evidence.get("status") != "COMPLETE_EVIDENCE_PACKAGE":
        errors.append("Evidence status must be COMPLETE_EVIDENCE_PACKAGE.")
    if not evidence.get("ready_for_shutdown"):
        errors.append("Evidence must be marked ready_for_shutdown.")
    if legacy_requests != 0:
        errors.append("Legacy `/api/*` traffic must be 0 requests.")
    if replacement_requests <= 0:
        errors.append("Replacement `/api/v1/*` active traffic must be confirmed.")
    if unknown_clients != 0:
        errors.append("Unknown clients must be 0.")
    if evidence.get("routes_changed") or evidence.get("proxy_modified"):
        errors.append("Evidence must be collected before route/proxy changes.")
    if evidence.get("legacy_code_removed") or evidence.get("database_archived"):
        errors.append("Evidence indicates unsafe destructive actions.")

    return errors


def evaluate_final_evidence(evidence_path=None, evidence=None):
    """Return READY_FOR_EXECUTION or BLOCKED_SAFELY for evidence only."""
    started_at = time.perf_counter()
    evidence_result = evidence or load_evidence(evidence_path)
    errors = []
    errors.extend(evidence_result.get("errors", []))
    errors.extend(validate_final_evidence(evidence_result))
    ready = not errors

    return {
        "status": "READY_FOR_EXECUTION" if ready else "BLOCKED_SAFELY",
        "evidence_ready": ready,
        "legacy_api": {
            "route": "/api/*",
            "required_requests": 0,
            "actual_requests": int(evidence_result.get("legacy_requests") or 0),
        },
        "replacement_api": {
            "route": "/api/v1/*",
            "active_traffic_confirmed": replacement_request_count(evidence_result) > 0,
            "actual_requests": replacement_request_count(evidence_result),
        },
        "unknown_clients": int(evidence_result.get("unknown_clients") or 0),
        "evidence_status": evidence_result.get("status", "UNKNOWN"),
        "errors": errors,
        "safety": {
            "legacy_api_disabled": False,
            "routes_changed": False,
            "iis_modified": False,
            "database_modified": False,
            "shutdown_executed": False,
        },
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
    }


def main():
    """Command line entrypoint for the final evidence validator."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.6.1 final production evidence validator")
    parser.add_argument("--evidence-report", default=None, help="Path to production evidence JSON report.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when evidence is blocked. Default blocked state exits 0.",
    )
    args = parser.parse_args()
    result = evaluate_final_evidence(evidence_path=args.evidence_report)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["evidence_ready"]:
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
