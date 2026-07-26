"""Validate Legacy API shutdown approval package for Phase 11.1.6.3.

This script only reads approval documents. It does not execute shutdown,
disable Legacy API, modify IIS, change routing, modify databases or alter
production configuration.
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

REQUIRED_DOCUMENTS = {
    "technical_approval": {
        "filename": "TECHNICAL_APPROVAL.md",
        "fields": [
            "System owner",
            "Technical reviewer",
            "Evidence confirmation",
            "Risk assessment",
            "Rollback validation",
            "Approval status",
            "Signature",
            "Date",
        ],
    },
    "business_approval": {
        "filename": "BUSINESS_APPROVAL.md",
        "fields": [
            "Business owner",
            "Business impact review",
            "Customer impact assessment",
            "Downtime acceptance",
            "Approval status",
            "Signature",
            "Date",
        ],
    },
    "rollback_owner": {
        "filename": "ROLLBACK_OWNER.md",
        "fields": [
            "Rollback owner",
            "Backup owner",
            "Rollback procedure reference",
            "Contact information",
            "Approval status",
            "Signature",
            "Date",
        ],
    },
    "maintenance_window": {
        "filename": "MAINTENANCE_WINDOW.md",
        "fields": [
            "Planned execution date",
            "Start time",
            "End time",
            "Timezone",
            "Expected impact",
            "Communication plan",
            "Rollback decision time",
            "Approval status",
            "Signature",
            "Date",
        ],
    },
    "monitoring_owner": {
        "filename": "MONITORING_OWNER.md",
        "fields": [
            "Monitoring owner",
            "Monitoring tools",
            "API errors metric",
            "Latency metric",
            "Traffic metric",
            "HTTP status codes metric",
            "Escalation path",
            "Approval status",
            "Signature",
            "Date",
        ],
    },
}

APPROVED_VALUES = {"approved", "complete", "completed", "assigned", "ready", "signed", "accepted"}
PENDING_VALUES = {"pending", "tbd", "missing", "not_provided", "not provided", "n/a", ""}


def read_field(content, field_name):
    """Read a `Field: value` entry from a markdown approval document."""
    pattern = re.compile(rf"^{re.escape(field_name)}\s*:\s*(?P<value>.+)$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(content)
    return match.group("value").strip() if match else ""


def is_meaningful(value):
    """Return True when value is not a placeholder."""
    return str(value or "").strip().lower() not in PENDING_VALUES


def validate_document(path, required_fields):
    """Validate one approval document."""
    document_path = Path(path)
    if not document_path.exists():
        return {
            "complete": False,
            "path": str(document_path),
            "fields": {},
            "errors": [f"Approval document does not exist: {document_path}."],
        }

    content = document_path.read_text(encoding="utf-8", errors="ignore")
    field_values = {field: read_field(content, field) for field in required_fields}
    errors = []

    for field, value in field_values.items():
        if not is_meaningful(value):
            errors.append(f"{field} is missing or pending.")

    approval_status = field_values.get("Approval status", "")
    if approval_status.strip().lower() not in APPROVED_VALUES:
        errors.append("Approval status is not approved/complete/assigned/ready/signed.")

    return {
        "complete": not errors,
        "path": str(document_path),
        "fields": field_values,
        "errors": errors,
    }


def validate_approval_package(approval_dir=None):
    """Validate the complete approval package."""
    started_at = time.perf_counter()
    directory = Path(approval_dir or DEFAULT_APPROVAL_DIR)
    documents = {}
    errors = []

    for key, config in REQUIRED_DOCUMENTS.items():
        result = validate_document(directory / config["filename"], config["fields"])
        documents[key] = result
        errors.extend([f"{key}: {error}" for error in result["errors"]])

    complete = not errors
    return {
        "status": "APPROVAL_COMPLETE" if complete else "APPROVAL_PENDING",
        "approval_complete": complete,
        "approval_dir": str(directory),
        "documents": documents,
        "missing_information": errors,
        "execution_readiness": "READY_FOR_EXECUTION_APPROVAL" if complete else "BLOCKED_SAFELY",
        "safety": {
            "shutdown_executed": False,
            "legacy_api_disabled": False,
            "iis_modified": False,
            "routes_changed": False,
            "database_modified": False,
            "production_configuration_changed": False,
        },
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
    }


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.6.3 approval package validator")
    parser.add_argument("--approval-dir", default=None, help="Approval package directory.")
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
