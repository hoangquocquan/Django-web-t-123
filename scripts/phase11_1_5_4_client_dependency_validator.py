"""Validate client dependency evidence for Phase 11.1.5.4."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLIENT_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "migration"
    / "production_evidence"
    / "clients"
    / "CLIENT_DEPENDENCY_MATRIX.csv"
)
READY_VALUES = {"0", "none", "false", "no"}
CONFIRMED_VALUES = {"confirmed", "yes", "true", "completed", "approved", "done"}
INCOMPLETE_VALUES = {"", "pending", "todo", "missing", "not_provided"}


def is_complete_value(value):
    """Return True when a CSV value is not a placeholder."""
    return str(value or "").strip().lower() not in INCOMPLETE_VALUES


def validate_client_rows(rows):
    """Validate client dependency rows."""
    errors = []
    for index, row in enumerate(rows, start=2):
        client = row.get("client") or f"row {index}"
        owner = row.get("owner")
        legacy_usage = str(row.get("legacy_api_usage") or "").strip().lower()
        replacement = row.get("replacement_api")
        migration_date = row.get("migration_date")
        confirmation = str(row.get("confirmation") or "").strip().lower()

        if not is_complete_value(owner):
            errors.append(f"{client}: owner is missing.")
        if legacy_usage not in READY_VALUES:
            errors.append(f"{client}: legacy API usage is not confirmed as zero.")
        if not is_complete_value(replacement):
            errors.append(f"{client}: replacement API is missing.")
        if not is_complete_value(migration_date):
            errors.append(f"{client}: migration date is missing.")
        if confirmation not in CONFIRMED_VALUES:
            errors.append(f"{client}: confirmation is missing.")
    return errors


def validate_client_dependencies(matrix_path=None):
    """Validate client migration confirmation matrix."""
    path = Path(matrix_path or DEFAULT_CLIENT_MATRIX)
    if not path.exists():
        return {
            "status": "CLIENT_MIGRATION_REQUIRED",
            "clients_ready": False,
            "matrix_path": str(path),
            "clients_checked": 0,
            "errors": [f"Client dependency matrix does not exist: {path}."],
        }

    with path.open("r", encoding="utf-8", errors="ignore", newline="") as file:
        rows = list(csv.DictReader(file))

    errors = []
    if not rows:
        errors.append("Client dependency matrix has no data rows.")
    errors.extend(validate_client_rows(rows))
    ready = not errors
    return {
        "status": "CLIENTS_READY" if ready else "CLIENT_MIGRATION_REQUIRED",
        "clients_ready": ready,
        "matrix_path": str(path),
        "clients_checked": len(rows),
        "errors": errors,
    }


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Phase 11.1.5.4 client dependency validator")
    parser.add_argument("--matrix", default=None, help="Client dependency CSV path.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when clients are not ready.")
    args = parser.parse_args()
    result = validate_client_dependencies(args.matrix)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["clients_ready"]:
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
