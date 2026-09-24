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
    from scripts.check_phase10_postgres_connection import (
        check_postgres_connection,
        evaluate_postgres_environment,
        is_postgresql_url,
        is_safe_test_database_url,
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
    from check_phase10_postgres_connection import (
        check_postgres_connection,
        evaluate_postgres_environment,
        is_postgresql_url,
        is_safe_test_database_url,
        mask_database_url,
        validate_dryrun_database_url,
    )


DRY_RUN_SCHEMA = "phase10_dry_run"
SURROGATE_LINK_TABLES = {
    "product_materials",
    "product_processes",
    "capability_machines",
}


def quote_sqlite_identifier(identifier):
    """Quote an SQLite identifier from the internal migration whitelist."""
    return '"' + identifier.replace('"', '""') + '"'


def get_sqlite_columns(cursor, table_name):
    """Return SQLite column metadata for one legacy table."""
    cursor.execute(f"PRAGMA table_info({quote_sqlite_identifier(table_name)})")
    return [
        {
            "cid": row[0],
            "name": row[1],
            "type": row[2],
            "notnull": bool(row[3]),
            "default": row[4],
            "pk": row[5],
        }
        for row in cursor.fetchall()
    ]


def get_sqlite_foreign_keys(cursor, table_name):
    """Return SQLite foreign-key metadata for one legacy table."""
    cursor.execute(f"PRAGMA foreign_key_list({quote_sqlite_identifier(table_name)})")
    return [
        {
            "id": row[0],
            "seq": row[1],
            "table": row[2],
            "from": row[3],
            "to": row[4],
            "on_update": row[5],
            "on_delete": row[6],
        }
        for row in cursor.fetchall()
    ]


def map_sqlite_type_to_postgres(sqlite_type):
    """Map simple SQLite column types into PostgreSQL dry-run types."""
    normalized = (sqlite_type or "").upper()
    if "INT" in normalized:
        return "BIGINT"
    if "REAL" in normalized or "FLOA" in normalized or "DOUB" in normalized:
        return "NUMERIC"
    return "TEXT"


def target_columns_for_table(columns, table_name):
    """Build PostgreSQL column definitions for the dry-run target table."""
    target_columns = []
    if table_name in SURROGATE_LINK_TABLES:
        target_columns.append({"name": "id", "type": "BIGSERIAL", "primary_key": True})

    for column in columns:
        is_single_id_pk = column["name"] == "id" and column["pk"] == 1
        target_columns.append(
            {
                "name": column["name"],
                "type": "BIGINT" if is_single_id_pk else map_sqlite_type_to_postgres(column["type"]),
                "primary_key": is_single_id_pk and table_name not in SURROGATE_LINK_TABLES,
                "notnull": column["notnull"],
            }
        )
    return target_columns


def create_target_table(cursor, schema_name, table_name, columns):
    """Create a PostgreSQL target table inside the rollback-only dry-run schema."""
    target_columns = target_columns_for_table(columns, table_name)
    column_parts = []
    for column in target_columns:
        part = sql.SQL("{} {}").format(sql.Identifier(column["name"]), sql.SQL(column["type"]))
        if column.get("primary_key"):
            part += sql.SQL(" PRIMARY KEY")
        elif column.get("notnull"):
            part += sql.SQL(" NOT NULL")
        column_parts.append(part)

    cursor.execute(
        sql.SQL("CREATE TABLE {}.{} ({})").format(
            sql.Identifier(schema_name),
            sql.Identifier(table_name),
            sql.SQL(", ").join(column_parts),
        )
    )


def add_target_constraints(cursor, schema_name, table_name, columns, foreign_keys):
    """Add unique and foreign-key constraints after all target tables exist."""
    pk_columns = [column["name"] for column in sorted(columns, key=lambda item: item["pk"]) if column["pk"]]
    if table_name in SURROGATE_LINK_TABLES and pk_columns:
        cursor.execute(
            sql.SQL("ALTER TABLE {}.{} ADD CONSTRAINT {} UNIQUE ({})").format(
                sql.Identifier(schema_name),
                sql.Identifier(table_name),
                sql.Identifier(f"uq_{table_name}_{'_'.join(pk_columns)}"),
                sql.SQL(", ").join(sql.Identifier(column_name) for column_name in pk_columns),
            )
        )
    elif len(pk_columns) > 1:
        cursor.execute(
            sql.SQL("ALTER TABLE {}.{} ADD CONSTRAINT {} PRIMARY KEY ({})").format(
                sql.Identifier(schema_name),
                sql.Identifier(table_name),
                sql.Identifier(f"pk_{table_name}"),
                sql.SQL(", ").join(sql.Identifier(column_name) for column_name in pk_columns),
            )
        )

    for index, foreign_key in enumerate(foreign_keys, start=1):
        if foreign_key["table"] not in EXPECTED_TABLES:
            continue
        cursor.execute(
            sql.SQL(
                "ALTER TABLE {}.{} ADD CONSTRAINT {} FOREIGN KEY ({}) "
                "REFERENCES {}.{} ({})"
            ).format(
                sql.Identifier(schema_name),
                sql.Identifier(table_name),
                sql.Identifier(f"fk_{table_name}_{foreign_key['from']}_{index}"),
                sql.Identifier(foreign_key["from"]),
                sql.Identifier(schema_name),
                sql.Identifier(foreign_key["table"]),
                sql.Identifier(foreign_key["to"]),
            )
        )


def fetch_legacy_rows(sqlite_cursor, table_name):
    """Read all legacy rows for one table from the read-only SQLite connection."""
    sqlite_cursor.execute(f"SELECT * FROM {quote_sqlite_identifier(table_name)}")
    column_names = [description[0] for description in sqlite_cursor.description]
    return column_names, sqlite_cursor.fetchall()


def insert_rows(cursor, schema_name, table_name, column_names, rows):
    """Insert copied rows into the PostgreSQL dry-run target table."""
    if not rows:
        return 0

    insert_sql = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
        sql.Identifier(schema_name),
        sql.Identifier(table_name),
        sql.SQL(", ").join(sql.Identifier(column_name) for column_name in column_names),
        sql.SQL(", ").join(sql.Placeholder() for _ in column_names),
    )
    cursor.executemany(insert_sql, rows)
    return len(rows)


def count_postgres_rows(cursor, schema_name, table_name):
    """Count rows in one PostgreSQL target table."""
    cursor.execute(
        sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
            sql.Identifier(schema_name),
            sql.Identifier(table_name),
        )
    )
    return cursor.fetchone()[0]


def validate_foreign_keys(sqlite_cursor):
    """Validate foreign keys inside the legacy source before copying rows."""
    sqlite_cursor.execute("PRAGMA foreign_key_check")
    return sqlite_cursor.fetchall()


def validate_composite_pairs(sqlite_cursor, table_name, columns):
    """Check duplicate legacy composite-key pairs before surrogate target import."""
    pk_columns = [column["name"] for column in sorted(columns, key=lambda item: item["pk"]) if column["pk"]]
    if table_name not in SURROGATE_LINK_TABLES or not pk_columns:
        return []

    sqlite_cursor.execute(
        "SELECT {columns}, COUNT(*) FROM {table} GROUP BY {columns} HAVING COUNT(*) > 1".format(
            columns=", ".join(quote_sqlite_identifier(column) for column in pk_columns),
            table=quote_sqlite_identifier(table_name),
        )
    )
    return sqlite_cursor.fetchall()


def execute_dry_run(database_url=None, sqlite_database=DEFAULT_DATABASE, schema_name=DRY_RUN_SCHEMA):
    """Run a full rollback-only PostgreSQL dry-run migration simulation."""
    if sql is None:
        raise RuntimeError("psycopg is required for PostgreSQL dry-run execution.")

    database_url = database_url or os.getenv("PHASE10_DRY_RUN_DATABASE_URL", "")
    readiness = evaluate_dry_run(database_url)
    connection_check = check_postgres_connection(database_url)
    if not readiness["dry_run_allowed"] or not connection_check["connection_ok"]:
        return {
            "status": "blocked",
            "dry_run_executed": False,
            "errors": readiness["errors"] + connection_check["errors"],
            "readiness": readiness,
            "connection": connection_check,
        }

    import psycopg

    started_at = time.perf_counter()
    legacy_snapshot_before = snapshot_database(Path(sqlite_database))
    copied_rows = {}
    target_rows = {}
    validation_errors = []
    rollback_confirmed = False

    try:
        with connect_readonly(Path(sqlite_database)) as sqlite_connection:
            sqlite_cursor = sqlite_connection.cursor()
            foreign_key_violations = validate_foreign_keys(sqlite_cursor)
            if foreign_key_violations:
                validation_errors.append(
                    f"Legacy foreign-key violations found: {len(foreign_key_violations)}"
                )

            table_metadata = {}
            for table_name in EXPECTED_TABLES:
                columns = get_sqlite_columns(sqlite_cursor, table_name)
                duplicate_pairs = validate_composite_pairs(sqlite_cursor, table_name, columns)
                if duplicate_pairs:
                    validation_errors.append(
                        f"Duplicate composite pairs found in {table_name}: {len(duplicate_pairs)}"
                    )
                table_metadata[table_name] = {
                    "columns": columns,
                    "foreign_keys": get_sqlite_foreign_keys(sqlite_cursor, table_name),
                }

            with psycopg.connect(database_url, connect_timeout=5) as postgres_connection:
                postgres_connection.autocommit = False
                with postgres_connection.cursor() as pg_cursor:
                    pg_cursor.execute(
                        sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                            sql.Identifier(schema_name)
                        )
                    )
                    pg_cursor.execute(
                        sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name))
                    )

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
                        copied_rows[table_name] = insert_rows(
                            pg_cursor,
                            schema_name,
                            table_name,
                            column_names,
                            rows,
                        )
                        target_rows[table_name] = count_postgres_rows(
                            pg_cursor,
                            schema_name,
                            table_name,
                        )

                    for table_name, source_count in legacy_snapshot_before["row_counts"].items():
                        if target_rows.get(table_name) != source_count:
                            validation_errors.append(
                                f"Row-count mismatch for {table_name}: "
                                f"source={source_count}, target={target_rows.get(table_name)}"
                            )

                    postgres_connection.rollback()
                    rollback_confirmed = True

                    pg_cursor.execute(
                        "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                        (schema_name,),
                    )
                    schema_exists_after_rollback = pg_cursor.fetchone() is not None
                    if schema_exists_after_rollback:
                        validation_errors.append(
                            f"Rollback did not remove schema {schema_name}."
                        )
    except Exception as exc:
        validation_errors.append(str(exc))

    elapsed_seconds = round(time.perf_counter() - started_at, 4)
    legacy_snapshot_after = snapshot_database(Path(sqlite_database))
    status = "completed" if not validation_errors and rollback_confirmed else "failed"
    return {
        "status": status,
        "dry_run_executed": True,
        "target_database_url": mask_database_url(database_url),
        "target_schema": schema_name,
        "elapsed_seconds": elapsed_seconds,
        "connection": connection_check,
        "legacy_snapshot_before": legacy_snapshot_before,
        "legacy_snapshot_after": legacy_snapshot_after,
        "legacy_database_unchanged": (
            legacy_snapshot_before["database_size_bytes"]
            == legacy_snapshot_after["database_size_bytes"]
            and legacy_snapshot_after["database_size_unchanged"]
        ),
        "copied_rows": copied_rows,
        "target_rows": target_rows,
        "validation_errors": validation_errors,
        "rollback": {
            "transaction_rollback_executed": rollback_confirmed,
            "target_schema_persisted": False if rollback_confirmed and not validation_errors else None,
        },
        "execution": {
            "postgresql_schema_created": rollback_confirmed,
            "django_migrations_generated": False,
            "data_import_executed": bool(copied_rows),
            "production_touched": False,
        },
    }


def evaluate_dry_run(database_url=None, legacy_database_path=DEFAULT_DATABASE):
    """Evaluate whether Phase 10.2 can run against a safe test target."""
    database_url = database_url or os.getenv("PHASE10_DRY_RUN_DATABASE_URL", "")
    snapshot = snapshot_database(Path(legacy_database_path))
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
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run rollback-only PostgreSQL migration simulation",
    )
    parser.add_argument(
        "--sqlite-database",
        default=str(DEFAULT_DATABASE),
        help="Legacy SQLite source database opened in read-only mode",
    )
    args = parser.parse_args()
    if args.execute:
        result = execute_dry_run(args.database_url, Path(args.sqlite_database))
    else:
        result = evaluate_dry_run(args.database_url, Path(args.sqlite_database))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.execute:
        return 0 if result["status"] == "completed" else 2
    return 0 if result["dry_run_allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
