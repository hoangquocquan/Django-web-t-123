"""Phase 10.3 data reconciliation for the PostgreSQL dry-run target.

This script compares the read-only legacy SQLite source with a rollback-only
PostgreSQL dry-run target. It validates counts, checksums, relationships,
orphans and basic business rules without keeping target data after execution.
"""

from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
import os
import time
from pathlib import Path

try:
    from psycopg import sql
except ImportError:  # pragma: no cover - validated at runtime.
    sql = None

try:
    from scripts.phase10_readiness_snapshot import (
        DEFAULT_DATABASE,
        EXPECTED_TABLES,
        connect_readonly,
        snapshot_database,
    )
    from scripts.phase10_dry_run_migration import (
        DRY_RUN_SCHEMA,
        add_target_constraints,
        count_postgres_rows,
        create_target_table,
        fetch_legacy_rows,
        get_sqlite_columns,
        get_sqlite_foreign_keys,
        insert_rows,
        quote_sqlite_identifier,
        validate_composite_pairs,
        validate_foreign_keys,
    )
    from scripts.check_phase10_postgres_connection import (
        check_postgres_connection,
        mask_database_url,
        validate_dryrun_database_url,
    )
except ImportError:  # pragma: no cover - used when running this file directly.
    from phase10_readiness_snapshot import (
        DEFAULT_DATABASE,
        EXPECTED_TABLES,
        connect_readonly,
        snapshot_database,
    )
    from phase10_dry_run_migration import (
        DRY_RUN_SCHEMA,
        add_target_constraints,
        count_postgres_rows,
        create_target_table,
        fetch_legacy_rows,
        get_sqlite_columns,
        get_sqlite_foreign_keys,
        insert_rows,
        quote_sqlite_identifier,
        validate_composite_pairs,
        validate_foreign_keys,
    )
    from check_phase10_postgres_connection import (
        check_postgres_connection,
        mask_database_url,
        validate_dryrun_database_url,
    )


SENSITIVE_COLUMN_MARKERS = {
    "password",
    "token",
    "session",
    "challenge",
    "code",
}


def is_sensitive_column(column_name):
    """Return True when a column should be excluded from value-level reports."""
    lowered = column_name.lower()
    return any(marker in lowered for marker in SENSITIVE_COLUMN_MARKERS)


def normalize_value(value):
    """Normalize values before checksum generation."""
    if value is None:
        return "<NULL>"
    if isinstance(value, Decimal):
        normalized = value.normalize()
        return format(normalized, "f").rstrip("0").rstrip(".") or "0"
    if isinstance(value, float):
        return format(value, ".15g")
    return str(value)


def checksum_rows(column_names, rows):
    """Create a deterministic checksum without exposing row values."""
    safe_indexes = [
        index
        for index, column_name in enumerate(column_names)
        if not is_sensitive_column(column_name)
    ]
    hasher = hashlib.sha256()
    for row in rows:
        safe_values = [normalize_value(row[index]) for index in safe_indexes]
        hasher.update("\x1f".join(safe_values).encode("utf-8"))
        hasher.update(b"\n")
    return hasher.hexdigest()


def source_table_checksum(sqlite_cursor, table_name):
    """Return a source checksum for one SQLite table."""
    column_names, rows = fetch_legacy_rows(sqlite_cursor, table_name)
    return checksum_rows(column_names, rows)


def target_table_checksum(pg_cursor, schema_name, table_name, source_column_names):
    """Return a target checksum for one PostgreSQL table."""
    pg_cursor.execute(
        sql.SQL("SELECT {} FROM {}.{}").format(
            sql.SQL(", ").join(sql.Identifier(column_name) for column_name in source_column_names),
            sql.Identifier(schema_name),
            sql.Identifier(table_name),
        )
    )
    column_names = [description.name for description in pg_cursor.description]
    rows = pg_cursor.fetchall()
    return checksum_rows(column_names, rows)


def validate_sqlite_orphans(sqlite_cursor):
    """Detect orphan rows using SQLite's foreign-key checker."""
    return validate_foreign_keys(sqlite_cursor)


def validate_business_rules(sqlite_cursor):
    """Validate domain rules that should hold before cutover planning."""
    checks = {}

    business_queries = {
        "products_have_category": """
            SELECT COUNT(*)
            FROM products
            LEFT JOIN product_categories ON product_categories.id = products.category_id
            WHERE product_categories.id IS NULL
        """,
        "published_products_have_slug": """
            SELECT COUNT(*)
            FROM products
            WHERE status = 'published' AND (slug IS NULL OR TRIM(slug) = '')
        """,
        "contact_requests_have_contact": """
            SELECT COUNT(*)
            FROM contact_requests
            WHERE contact IS NULL OR TRIM(contact) = ''
        """,
        "quote_requests_have_customer": """
            SELECT COUNT(*)
            FROM quote_requests
            LEFT JOIN customers ON customers.id = quote_requests.customer_id
            WHERE customers.id IS NULL
        """,
        "cms_pages_have_slug": """
            SELECT COUNT(*)
            FROM cms_pages
            WHERE slug IS NULL OR TRIM(slug) = ''
        """,
        "active_admin_users_have_email": """
            SELECT COUNT(*)
            FROM admin_users
            WHERE is_active = 1 AND (email IS NULL OR TRIM(email) = '')
        """,
    }

    for check_name, query in business_queries.items():
        sqlite_cursor.execute(query)
        violation_count = sqlite_cursor.fetchone()[0]
        checks[check_name] = {
            "violations": violation_count,
            "result": "PASS" if violation_count == 0 else "FAIL",
        }
    return checks


def prepare_target_schema(pg_cursor, sqlite_cursor, schema_name):
    """Create dry-run target schema and load source rows for comparison."""
    table_metadata = {}
    for table_name in EXPECTED_TABLES:
        columns = get_sqlite_columns(sqlite_cursor, table_name)
        table_metadata[table_name] = {
            "columns": columns,
            "foreign_keys": get_sqlite_foreign_keys(sqlite_cursor, table_name),
        }

    pg_cursor.execute(
        sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema_name))
    )
    pg_cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name)))

    for table_name in EXPECTED_TABLES:
        create_target_table(
            pg_cursor,
            schema_name,
            table_name,
            table_metadata[table_name]["columns"],
        )

    for table_name in EXPECTED_TABLES:
        add_target_constraints(
            pg_cursor,
            schema_name,
            table_name,
            table_metadata[table_name]["columns"],
            table_metadata[table_name]["foreign_keys"],
        )

    for table_name in EXPECTED_TABLES:
        column_names, rows = fetch_legacy_rows(sqlite_cursor, table_name)
        insert_rows(pg_cursor, schema_name, table_name, column_names, rows)

    return table_metadata


def reconcile_data(database_url=None, sqlite_database=DEFAULT_DATABASE, schema_name=DRY_RUN_SCHEMA):
    """Run Phase 10.3 reconciliation and return a structured result."""
    if sql is None:
        raise RuntimeError("psycopg is required for Phase 10.3 reconciliation.")

    database_url = database_url or os.getenv("PHASE10_DRY_RUN_DATABASE_URL", "")
    url_validation = validate_dryrun_database_url(database_url)
    connection_check = check_postgres_connection(database_url)
    if url_validation["errors"] or not connection_check["connection_ok"]:
        return {
            "status": "blocked",
            "errors": url_validation["errors"] + connection_check["errors"],
            "target_database_url": mask_database_url(database_url),
            "connection": connection_check,
        }

    import psycopg

    started_at = time.perf_counter()
    errors = []
    row_count_results = {}
    checksum_results = {}
    composite_results = {}
    orphan_results = {}
    business_rule_results = {}
    rollback_confirmed = False

    legacy_snapshot_before = snapshot_database(Path(sqlite_database))

    try:
        with connect_readonly(Path(sqlite_database)) as sqlite_connection:
            sqlite_cursor = sqlite_connection.cursor()
            orphan_rows = validate_sqlite_orphans(sqlite_cursor)
            orphan_results = {
                "violations": len(orphan_rows),
                "result": "PASS" if not orphan_rows else "FAIL",
            }
            if orphan_rows:
                errors.append(f"SQLite foreign-key orphan rows found: {len(orphan_rows)}")

            business_rule_results = validate_business_rules(sqlite_cursor)
            for check_name, check in business_rule_results.items():
                if check["result"] != "PASS":
                    errors.append(
                        f"Business rule failed: {check_name} ({check['violations']})"
                    )

            for table_name in EXPECTED_TABLES:
                columns = get_sqlite_columns(sqlite_cursor, table_name)
                duplicate_pairs = validate_composite_pairs(sqlite_cursor, table_name, columns)
                composite_results[table_name] = {
                    "duplicate_pairs": len(duplicate_pairs),
                    "result": "PASS" if not duplicate_pairs else "FAIL",
                }
                if duplicate_pairs:
                    errors.append(
                        f"Duplicate composite pairs found in {table_name}: {len(duplicate_pairs)}"
                    )

            with psycopg.connect(database_url, connect_timeout=5) as postgres_connection:
                postgres_connection.autocommit = False
                with postgres_connection.cursor() as pg_cursor:
                    prepare_target_schema(pg_cursor, sqlite_cursor, schema_name)

                    for table_name in EXPECTED_TABLES:
                        source_count = legacy_snapshot_before["row_counts"][table_name]
                        target_count = count_postgres_rows(pg_cursor, schema_name, table_name)
                        row_count_results[table_name] = {
                            "source": source_count,
                            "target": target_count,
                            "result": "PASS" if source_count == target_count else "FAIL",
                        }
                        if source_count != target_count:
                            errors.append(
                                f"Row-count mismatch for {table_name}: source={source_count}, target={target_count}"
                            )

                        source_column_names, _rows = fetch_legacy_rows(
                            sqlite_cursor,
                            table_name,
                        )
                        source_checksum = checksum_rows(source_column_names, _rows)
                        target_checksum = target_table_checksum(
                            pg_cursor,
                            schema_name,
                            table_name,
                            source_column_names,
                        )
                        checksum_results[table_name] = {
                            "source_checksum": source_checksum,
                            "target_checksum": target_checksum,
                            "result": "PASS" if source_checksum == target_checksum else "FAIL",
                        }
                        if source_checksum != target_checksum:
                            errors.append(f"Checksum mismatch for {table_name}")

                    postgres_connection.rollback()
                    rollback_confirmed = True

                    pg_cursor.execute(
                        "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                        (schema_name,),
                    )
                    if pg_cursor.fetchone() is not None:
                        errors.append(f"Rollback did not remove schema {schema_name}.")
    except Exception as exc:
        errors.append(str(exc))

    elapsed_seconds = round(time.perf_counter() - started_at, 4)
    legacy_snapshot_after = snapshot_database(Path(sqlite_database))
    status = "passed" if not errors and rollback_confirmed else "failed"
    return {
        "status": status,
        "target_database_url": mask_database_url(database_url),
        "target_schema": schema_name,
        "elapsed_seconds": elapsed_seconds,
        "connection": connection_check,
        "legacy_database_unchanged": (
            legacy_snapshot_before["database_size_bytes"]
            == legacy_snapshot_after["database_size_bytes"]
            and legacy_snapshot_after["database_size_unchanged"]
        ),
        "legacy_snapshot_before": legacy_snapshot_before,
        "legacy_snapshot_after": legacy_snapshot_after,
        "row_counts": row_count_results,
        "checksums": checksum_results,
        "relationships": {
            "orphans": orphan_results,
            "composite_pairs": composite_results,
        },
        "business_rules": business_rule_results,
        "rollback": {
            "transaction_rollback_executed": rollback_confirmed,
            "target_schema_persisted": False if rollback_confirmed and not errors else None,
        },
        "security": {
            "sensitive_values_printed": False,
            "passwords_tokens_sessions_masked": True,
        },
        "errors": errors,
    }


def main():
    """CLI entrypoint for Phase 10.3 reconciliation."""
    parser = argparse.ArgumentParser(description="Phase 10.3 data reconciliation")
    parser.add_argument(
        "--database-url",
        default=None,
        help="Non-production PostgreSQL dry-run database URL",
    )
    parser.add_argument(
        "--sqlite-database",
        default=str(DEFAULT_DATABASE),
        help="Legacy SQLite source database opened in read-only mode",
    )
    args = parser.parse_args()
    result = reconcile_data(args.database_url, Path(args.sqlite_database))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
