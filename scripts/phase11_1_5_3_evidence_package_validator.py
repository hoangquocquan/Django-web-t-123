"""Validate the Phase 11.1.5.3 production evidence package.

The validator checks required files and verifies that templates have been
completed with real evidence. It does not change routes, proxy rules, database
state or legacy code.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE_ROOT = PROJECT_ROOT / "docs" / "migration" / "production_evidence"
INCOMPLETE_MARKERS = {"PENDING", "TODO", "NOT_PROVIDED", "NOT VERIFIED", "MISSING"}

REQUIRED_FILES = {
    "traffic_summary": "traffic/LEGACY_API_TRAFFIC_LOG_SUMMARY.md",
    "traffic_export": "traffic/LEGACY_API_TRAFFIC_EXPORT_TEMPLATE.csv",
    "client_confirmation": "clients/CLIENT_MIGRATION_CONFIRMATION_TEMPLATE.md",
    "client_matrix": "clients/CLIENT_DEPENDENCY_MATRIX.csv",
    "technical_approval": "approvals/TECHNICAL_APPROVAL.md",
    "business_approval": "approvals/BUSINESS_APPROVAL.md",
    "rollback_owner": "approvals/ROLLBACK_OWNER.md",
    "maintenance_window": "approvals/MAINTENANCE_WINDOW.md",
    "monitoring_confirmation": "monitoring/MONITORING_READINESS_CONFIRMATION.md",
}


def has_incomplete_marker(text):
    """Return True when a document still contains placeholder evidence."""
    upper_text = str(text or "").upper()
    return any(marker in upper_text for marker in INCOMPLETE_MARKERS)


def validate_markdown_file(path):
    """Validate that a Markdown evidence file exists and has no placeholders."""
    if not path.exists():
        return [f"Missing required file: {path}."]
    content = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not content:
        return [f"Required file is empty: {path}."]
    if has_incomplete_marker(content):
        return [f"Required file still contains incomplete placeholders: {path}."]
    return []


def validate_csv_file(path):
    """Validate that a CSV evidence file exists, has rows and no placeholders."""
    if not path.exists():
        return [f"Missing required file: {path}."]
    try:
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as file:
            rows = list(csv.DictReader(file))
    except csv.Error as exc:
        return [f"CSV file is invalid: {path}: {exc}."]

    if not rows:
        return [f"CSV file has no data rows: {path}."]

    errors = []
    for row_number, row in enumerate(rows, start=2):
        values = [str(value or "").strip() for value in row.values()]
        if not all(values):
            errors.append(f"CSV row {row_number} has empty values: {path}.")
        if any(has_incomplete_marker(value) for value in values):
            errors.append(f"CSV row {row_number} still contains incomplete placeholders: {path}.")
    return errors


def validate_package(package_root=None):
    """Validate completeness of the production evidence package."""
    started_at = time.perf_counter()
    root = Path(package_root or DEFAULT_PACKAGE_ROOT)
    errors = []
    checked_files = []

    if not root.exists():
        return {
            "status": "INCOMPLETE_EVIDENCE_PACKAGE",
            "complete": False,
            "package_root": str(root),
            "required_files": len(REQUIRED_FILES),
            "checked_files": 0,
            "missing_requirements": [f"Evidence package root does not exist: {root}."],
            "legacy_routes_disabled": False,
            "routes_changed": False,
            "proxy_modified": False,
            "database_archived": False,
            "legacy_code_removed": False,
            "elapsed_seconds": round(time.perf_counter() - started_at, 4),
        }

    for label, relative_path in REQUIRED_FILES.items():
        path = root / relative_path
        checked_files.append({"label": label, "path": str(path)})
        if path.suffix.lower() == ".csv":
            errors.extend(validate_csv_file(path))
        else:
            errors.extend(validate_markdown_file(path))

    complete = not errors
    return {
        "status": "COMPLETE_EVIDENCE_PACKAGE" if complete else "INCOMPLETE_EVIDENCE_PACKAGE",
        "complete": complete,
        "package_root": str(root),
        "required_files": len(REQUIRED_FILES),
        "checked_files": len(checked_files),
        "checked_file_details": checked_files,
        "missing_requirements": errors,
        "legacy_routes_disabled": False,
        "routes_changed": False,
        "proxy_modified": False,
        "database_archived": False,
        "legacy_code_removed": False,
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
    }


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.5.3 evidence package validator")
    parser.add_argument("--root", default=None, help="Evidence package root folder.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when package is incomplete.")
    args = parser.parse_args()
    result = validate_package(args.root)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["complete"]:
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
