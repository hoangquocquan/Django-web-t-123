"""Final approval package validator for Phase 11.1.6.1.

The validator checks human approval templates. It never executes shutdown,
changes routes, edits IIS or modifies data.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APPROVAL_DIR = PROJECT_ROOT / "docs" / "migration" / "phase11_1_6_execution" / "approvals"
REQUIRED_APPROVALS = {
    "technical_approval": "TECHNICAL_APPROVAL.md",
    "business_approval": "BUSINESS_APPROVAL.md",
    "rollback_owner": "ROLLBACK_OWNER.md",
    "maintenance_window": "MAINTENANCE_WINDOW.md",
    "monitoring_owner": "MONITORING_OWNER.md",
}
APPROVED_VALUES = {"approved", "complete", "completed", "assigned", "ready", "signed"}
PENDING_VALUES = {"pending", "tbd", "missing", "not_provided", ""}


def read_field(content, field_name):
    """Read a simple `Field: value` entry from an approval document."""
    pattern = re.compile(rf"^{re.escape(field_name)}\s*:\s*(?P<value>.+)$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(content)
    return match.group("value").strip() if match else ""


def meaningful(value):
    """Return True when a field is not a placeholder."""
    return str(value or "").strip().lower() not in PENDING_VALUES


def approval_file_status(path):
    """Validate a single approval file."""
    approval_path = Path(path)
    if not approval_path.exists():
        return {
            "complete": False,
            "errors": [f"Approval file does not exist: {approval_path}."],
        }

    content = approval_path.read_text(encoding="utf-8", errors="ignore")
    owner = read_field(content, "Owner")
    date = read_field(content, "Date")
    status = read_field(content, "Approval status")
    signature = read_field(content, "Signature")

    errors = []
    if not meaningful(owner):
        errors.append("Owner is missing or pending.")
    if not meaningful(date):
        errors.append("Date is missing or pending.")
    if status.strip().lower() not in APPROVED_VALUES:
        errors.append("Approval status is not approved/complete/assigned/ready.")
    if not meaningful(signature):
        errors.append("Signature is missing or pending.")

    return {
        "complete": not errors,
        "owner": owner or None,
        "date": date or None,
        "approval_status": status or None,
        "signature": signature or None,
        "errors": errors,
    }


def validate_approval_package(approval_dir=None):
    """Return APPROVAL_COMPLETE or APPROVAL_PENDING."""
    started_at = time.perf_counter()
    directory = Path(approval_dir or DEFAULT_APPROVAL_DIR)
    file_results = {}
    errors = []

    for key, filename in REQUIRED_APPROVALS.items():
        result = approval_file_status(directory / filename)
        file_results[key] = result
        errors.extend([f"{key}: {error}" for error in result["errors"]])

    complete = not errors
    return {
        "status": "APPROVAL_COMPLETE" if complete else "APPROVAL_PENDING",
        "approval_complete": complete,
        "approval_dir": str(directory),
        "files": file_results,
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
    """Command line entrypoint for approval package validation."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.6.1 approval package validator")
    parser.add_argument("--approval-dir", default=None, help="Directory containing approval markdown files.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when approval is pending. Default pending state exits 0.",
    )
    args = parser.parse_args()
    result = validate_approval_package(approval_dir=args.approval_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["approval_complete"]:
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
