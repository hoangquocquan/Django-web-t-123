"""Phase 10.2 dry-run migration gate.

The script does not touch production. It validates whether a PostgreSQL test
target is configured, reads the legacy SQLite snapshot in read-only mode, and
returns a structured dry-run status. Real data import is intentionally blocked
unless a clearly non-production PostgreSQL URL is supplied.
"""

from __future__ import annotations

import os
import argparse
import json

try:
    from scripts.phase10_readiness_snapshot import snapshot_database
    from scripts.check_phase10_postgres_connection import (
        evaluate_postgres_environment,
        is_postgresql_url,
        is_safe_test_database_url,
        mask_database_url,
        validate_dryrun_database_url,
    )
except ImportError:  # pragma: no cover - used when running this file directly.
    from phase10_readiness_snapshot import snapshot_database
    from check_phase10_postgres_connection import (
        evaluate_postgres_environment,
        is_postgresql_url,
        is_safe_test_database_url,
        mask_database_url,
        validate_dryrun_database_url,
    )


def evaluate_dry_run(database_url=None):
    """Evaluate whether Phase 10.2 can run against a safe test target."""
    database_url = database_url or os.getenv("PHASE10_DRY_RUN_DATABASE_URL", "")
    snapshot = snapshot_database()
    url_validation = validate_dryrun_database_url(database_url)
    environment_validation = evaluate_postgres_environment(
        database_url,
        check_connection=False,
    )
    errors = url_validation["errors"]

    dry_run_allowed = not errors
    return {
        "status": "ready" if dry_run_allowed else "blocked",
        "dry_run_allowed": dry_run_allowed,
        "target_database_url": mask_database_url(database_url),
        "errors": errors,
        "environment_validation": {
            "status": environment_validation["status"],
            "database_name": url_validation["database_name"],
            "is_postgresql_url": url_validation["is_postgresql_url"],
            "is_safe_non_production_name": url_validation[
                "is_safe_non_production_name"
            ],
            "has_forbidden_database_name": url_validation[
                "has_forbidden_database_name"
            ],
            "production_touched": environment_validation["production_touched"],
        },
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
