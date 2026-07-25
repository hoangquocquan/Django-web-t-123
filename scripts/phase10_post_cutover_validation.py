"""Phase 10.5 post-cutover validation gate.

The script validates whether post-cutover checks are ready to run. Without an
explicit cutover-completed marker it reports a safe blocked status instead of
querying production or assuming traffic was switched.
"""

from __future__ import annotations

import argparse
import json
import os
from urllib.parse import urlparse

try:
    from scripts.phase10_readiness_snapshot import EXPECTED_TABLES
    from scripts.check_phase10_postgres_connection import (
        check_postgres_connection,
        mask_database_url,
    )
    from scripts.phase10_cutover_readiness import validate_production_database_url
except ImportError:  # pragma: no cover - used when running this file directly.
    from phase10_readiness_snapshot import EXPECTED_TABLES
    from check_phase10_postgres_connection import (
        check_postgres_connection,
        mask_database_url,
    )
    from phase10_cutover_readiness import validate_production_database_url


CUTOVER_COMPLETED_ENV = "PHASE10_CUTOVER_COMPLETED"
VALIDATION_DATABASE_URL_ENV = "PHASE10_PRODUCTION_DATABASE_URL"


def flag_enabled(value):
    """Return True when a validation flag is explicitly enabled."""
    return str(value or "").strip().lower() in {"1", "true", "yes", "completed"}


def validate_table_availability(database_url, expected_tables=None):
    """Validate expected table availability in a configured PostgreSQL database."""
    expected_tables = expected_tables or EXPECTED_TABLES
    try:
        import psycopg
    except ImportError:
        return {
            "checked": False,
            "available_tables": [],
            "missing_tables": expected_tables,
            "errors": ["psycopg is not installed."],
        }

    errors = []
    available_tables = []
    try:
        with psycopg.connect(database_url, connect_timeout=5) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    """
                )
                available_tables = sorted(row[0] for row in cursor.fetchall())
    except Exception as exc:  # pragma: no cover - depends on production env.
        errors.append(f"Post-cutover table availability check failed: {exc}")

    missing_tables = [
        table_name for table_name in expected_tables if table_name not in available_tables
    ]
    return {
        "checked": not errors,
        "available_tables": available_tables,
        "missing_tables": missing_tables,
        "errors": errors,
    }


def evaluate_post_cutover_validation(env=None):
    """Evaluate post-cutover validation readiness and results."""
    env = env or os.environ
    cutover_completed = flag_enabled(env.get(CUTOVER_COMPLETED_ENV))
    database_url = env.get(VALIDATION_DATABASE_URL_ENV, "")
    database_validation = validate_production_database_url(database_url)
    errors = []

    if not cutover_completed:
        errors.append(f"{CUTOVER_COMPLETED_ENV} is not set to completed.")
    errors.extend(database_validation["errors"])

    connection = {
        "connection_checked": False,
        "connection_ok": False,
        "errors": [],
    }
    tables = {
        "checked": False,
        "available_tables": [],
        "missing_tables": EXPECTED_TABLES,
        "errors": [],
    }

    if cutover_completed and not database_validation["errors"]:
        connection = check_postgres_connection(database_url)
        if connection["connection_ok"]:
            tables = validate_table_availability(database_url)
            errors.extend(tables["errors"])
            if tables["missing_tables"]:
                errors.append(
                    f"Missing expected production tables: {len(tables['missing_tables'])}"
                )
        else:
            errors.extend(connection["errors"])

    status = "passed" if cutover_completed and not errors else "blocked_safely"
    return {
        "status": status,
        "post_cutover_validation_executed": cutover_completed and not database_validation["errors"],
        "production_database_url": mask_database_url(database_url),
        "database": {
            "name": urlparse(database_url).path.lstrip("/") if database_url else "",
            "validation": database_validation,
            "connection": connection,
            "tables": tables,
        },
        "application": {
            "django_health": "run python manage.py check",
            "api_health": "run approved API smoke tests",
        },
        "business": {
            "catalog_access": "pending real cutover",
            "crm_access": "pending real cutover",
            "sales_access": "pending real cutover",
            "cms_access": "pending real cutover",
            "authentication": "pending real cutover",
        },
        "errors": errors,
    }


def main():
    """CLI entrypoint for Phase 10.5 post-cutover validation."""
    parser = argparse.ArgumentParser(description="Phase 10.5 post-cutover validation")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when validation is blocked. Default exits 0 for safe blocking.",
    )
    args = parser.parse_args()
    result = evaluate_post_cutover_validation()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] == "passed":
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
