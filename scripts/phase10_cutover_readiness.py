"""Phase 10.4 production database cutover readiness gate.

This script does not execute cutover. It only checks whether the documented
production prerequisites are present before a human-approved cutover window.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlparse

try:
    from scripts.check_phase10_postgres_connection import mask_database_url
except ImportError:  # pragma: no cover - used when running this file directly.
    from check_phase10_postgres_connection import mask_database_url


REQUIRED_FLAGS = {
    "PHASE10_MAINTENANCE_WINDOW_APPROVED": "maintenance window approval",
    "PHASE10_LEGACY_WRITE_FREEZE_APPROVED": "legacy write freeze approval",
    "PHASE10_ROLLBACK_APPROVED": "rollback plan approval",
    "PHASE10_FINAL_BACKUP_VERIFIED": "final backup verification",
}
REQUIRED_VALUES = {
    "PHASE10_PRODUCTION_DATABASE_URL": "production PostgreSQL database URL",
    "PHASE10_FINAL_BACKUP_PATH": "final legacy backup path",
    "PHASE10_FINAL_BACKUP_SHA256": "final backup SHA256 checksum",
    "PHASE10_ROLLBACK_OWNER": "assigned rollback owner",
    "PHASE10_CUTOVER_APPROVAL_ID": "cutover approval identifier",
}
NON_PRODUCTION_MARKERS = {"dryrun", "dry_run", "test", "staging", "dev"}
PRODUCTION_FORBIDDEN_DATABASE_NAMES = {"postgres", "template0", "template1"}


def env_flag_enabled(value):
    """Return True when an approval-style environment flag is explicitly enabled."""
    return str(value or "").strip().lower() in {"1", "true", "yes", "approved"}


def database_name_from_url(database_url):
    """Extract the database name from a PostgreSQL URL."""
    return urlparse(database_url).path.lstrip("/")


def validate_production_database_url(database_url):
    """Validate that a production URL looks like a real PostgreSQL production target."""
    errors = []
    parsed = urlparse(database_url or "")
    database_name = database_name_from_url(database_url or "").lower()

    if not database_url:
        errors.append("PHASE10_PRODUCTION_DATABASE_URL is not configured.")
    elif parsed.scheme not in {"postgres", "postgresql"}:
        errors.append("Production database URL must use postgres/postgresql scheme.")
    elif not database_name:
        errors.append("Production database URL must include a database name.")
    else:
        if database_name in PRODUCTION_FORBIDDEN_DATABASE_NAMES:
            errors.append("Production cutover must not target a system database.")
        if any(marker in database_name for marker in NON_PRODUCTION_MARKERS):
            errors.append(
                "Production cutover URL still points to a non-production database name."
            )

    return {
        "database_name": database_name,
        "masked_database_url": mask_database_url(database_url),
        "errors": errors,
    }


def sha256_file(path):
    """Return SHA256 checksum for a backup file."""
    hasher = hashlib.sha256()
    with Path(path).open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_backup(path_value, expected_sha256):
    """Validate final backup presence and checksum without creating files."""
    errors = []
    backup_path = Path(path_value) if path_value else None
    actual_sha256 = ""
    size_bytes = None

    if not path_value:
        errors.append("PHASE10_FINAL_BACKUP_PATH is not configured.")
    elif not backup_path.exists():
        errors.append(f"Final backup file does not exist: {path_value}")
    elif not backup_path.is_file():
        errors.append(f"Final backup path is not a file: {path_value}")
    else:
        size_bytes = backup_path.stat().st_size
        actual_sha256 = sha256_file(backup_path)
        if expected_sha256 and actual_sha256.lower() != expected_sha256.lower():
            errors.append("Final backup SHA256 checksum does not match.")

    if not expected_sha256:
        errors.append("PHASE10_FINAL_BACKUP_SHA256 is not configured.")

    return {
        "path": path_value or "",
        "exists": bool(backup_path and backup_path.exists()),
        "size_bytes": size_bytes,
        "actual_sha256": actual_sha256,
        "expected_sha256_configured": bool(expected_sha256),
        "errors": errors,
    }


def evaluate_cutover_readiness(env=None):
    """Evaluate all Phase 10.4 cutover prerequisites."""
    env = env or os.environ
    errors = []
    approvals = {}
    configured_values = {}

    for key, label in REQUIRED_FLAGS.items():
        enabled = env_flag_enabled(env.get(key))
        approvals[key] = {
            "label": label,
            "approved": enabled,
        }
        if not enabled:
            errors.append(f"Missing approval: {label} ({key}).")

    for key, label in REQUIRED_VALUES.items():
        value = env.get(key, "")
        configured_values[key] = bool(value)
        if not value:
            errors.append(f"Missing required value: {label} ({key}).")

    database_validation = validate_production_database_url(
        env.get("PHASE10_PRODUCTION_DATABASE_URL", "")
    )
    backup_validation = validate_backup(
        env.get("PHASE10_FINAL_BACKUP_PATH", ""),
        env.get("PHASE10_FINAL_BACKUP_SHA256", ""),
    )
    errors.extend(database_validation["errors"])
    errors.extend(backup_validation["errors"])

    ready = not errors
    return {
        "status": "ready" if ready else "blocked",
        "ready_for_cutover": ready,
        "production_cutover_executed": False,
        "production_database_switched": False,
        "legacy_writes_enabled": False,
        "database": database_validation,
        "backup": backup_validation,
        "approvals": approvals,
        "configured_values": configured_values,
        "rollback": {
            "owner": env.get("PHASE10_ROLLBACK_OWNER", ""),
            "approval_present": approvals["PHASE10_ROLLBACK_APPROVED"]["approved"],
            "traffic_route_back_plan_required": True,
        },
        "validation_gates": {
            "phase_10_3_reconciliation_required": True,
            "api_contract_tests_required": True,
            "smoke_tests_required": True,
            "post_cutover_monitoring_required": True,
        },
        "errors": errors,
    }


def main():
    """CLI entrypoint for Phase 10.4 cutover readiness."""
    parser = argparse.ArgumentParser(description="Phase 10.4 cutover readiness gate")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON output. This is the default and kept for clarity.",
    )
    _args = parser.parse_args()
    result = evaluate_cutover_readiness()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ready_for_cutover"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
