"""Phase 10.2 dry-run migration gate.

The script does not touch production. It validates whether a PostgreSQL test
target is configured, reads the legacy SQLite snapshot in read-only mode, and
returns a structured dry-run status. Real data import is intentionally blocked
unless a clearly non-production PostgreSQL URL is supplied.
"""

from __future__ import annotations

import argparse
import json
import os
from urllib.parse import urlparse

try:
    from scripts.phase10_readiness_snapshot import snapshot_database
except ImportError:  # pragma: no cover - used when running this file directly.
    from phase10_readiness_snapshot import snapshot_database


SAFE_DATABASE_NAME_MARKERS = {"test", "dryrun", "dry_run", "staging", "dev"}


def mask_database_url(database_url):
    """Mask credentials before including a URL in reports."""
    if not database_url:
        return ""

    parsed = urlparse(database_url)
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    username = parsed.username or ""
    auth = f"{username}:***@" if username else ""
    return f"{parsed.scheme}://{auth}{host}{port}{parsed.path}"


def is_postgresql_url(database_url):
    """Return True when the URL points to PostgreSQL."""
    return urlparse(database_url).scheme in {"postgres", "postgresql"}


def is_safe_test_database_url(database_url):
    """Allow only clearly non-production target database names."""
    parsed = urlparse(database_url)
    database_name = parsed.path.lstrip("/").lower()
    return any(marker in database_name for marker in SAFE_DATABASE_NAME_MARKERS)


def evaluate_dry_run(database_url=None):
    """Evaluate whether Phase 10.2 can run against a safe test target."""
    database_url = database_url or os.getenv("PHASE10_DRY_RUN_DATABASE_URL", "")
    snapshot = snapshot_database()
    errors = []

    if not database_url:
        errors.append("PHASE10_DRY_RUN_DATABASE_URL is not configured.")
    elif not is_postgresql_url(database_url):
        errors.append("Dry-run target must use postgres/postgresql URL scheme.")
    elif not is_safe_test_database_url(database_url):
        errors.append("Dry-run database name must include test, dryrun, staging or dev.")

    dry_run_allowed = not errors
    return {
        "status": "ready" if dry_run_allowed else "blocked",
        "dry_run_allowed": dry_run_allowed,
        "target_database_url": mask_database_url(database_url),
        "errors": errors,
        "legacy_snapshot": {
            "database_size_bytes": snapshot["database_size_bytes"],
            "database_size_unchanged": snapshot["database_size_unchanged"],
            "expected_table_count": snapshot["expected_table_count"],
            "found_table_count": snapshot["found_table_count"],
            "missing_tables": snapshot["missing_tables"],
            "row_counts": snapshot["row_counts"],
        },
        "execution": {
            "postgresql_schema_created": False,
            "django_migrations_generated": False,
            "data_import_executed": False,
            "production_touched": False,
        },
    }


def main():
    """CLI entrypoint for Phase 10.2 dry-run readiness."""
    parser = argparse.ArgumentParser(description="Phase 10.2 dry-run migration gate")
    parser.add_argument(
        "--database-url",
        default=None,
        help="Non-production PostgreSQL dry-run database URL",
    )
    args = parser.parse_args()
    result = evaluate_dry_run(args.database_url)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["dry_run_allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
