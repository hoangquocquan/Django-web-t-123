"""Create a read-only Phase 10 legacy database readiness snapshot.

This script is intentionally safe: it opens the legacy SQLite database with
`mode=ro`, counts expected tables, and prints JSON to stdout. It does not create
tables, run migrations, write data, or connect to production PostgreSQL.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = PROJECT_ROOT / "backend" / "database" / "mecprecision.sqlite"

EXPECTED_TABLES = [
    "product_categories",
    "materials",
    "machines",
    "manufacturing_processes",
    "capabilities",
    "products",
    "product_images",
    "product_specs",
    "product_materials",
    "product_processes",
    "capability_machines",
    "customers",
    "customer_notes",
    "contact_requests",
    "quote_requests",
    "quote_request_items",
    "quote_files",
    "cms_pages",
    "cms_menu_items",
    "cms_banners",
    "newsletter_subscribers",
    "admin_users",
    "admin_sessions",
    "login_attempts",
    "password_reset_tokens",
    "admin_2fa_challenges",
    "admin_activity_logs",
]


def connect_readonly(database_path: Path):
    """Open SQLite with read-only URI mode."""
    uri = f"file:{database_path.as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def table_exists(cursor, table_name):
    """Return True when a table exists in sqlite_master."""
    return (
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type = ? AND name = ?",
            ("table", table_name),
        ).fetchone()
        is not None
    )


def snapshot_database(database_path: Path = DEFAULT_DATABASE):
    """Return row-count and dependency readiness metadata."""
    database_path = database_path.resolve()
    if not database_path.exists():
        raise FileNotFoundError(f"Legacy database not found: {database_path}")

    before_size = database_path.stat().st_size
    row_counts = {}
    missing_tables = []

    with connect_readonly(database_path) as connection:
        cursor = connection.cursor()
        for table_name in EXPECTED_TABLES:
            if table_exists(cursor, table_name):
                row_counts[table_name] = cursor.execute(
                    f"SELECT COUNT(*) FROM {table_name}"
                ).fetchone()[0]
            else:
                missing_tables.append(table_name)

    after_size = database_path.stat().st_size
    return {
        "database_path": str(database_path),
        "database_size_bytes": before_size,
        "database_size_unchanged": before_size == after_size,
        "expected_table_count": len(EXPECTED_TABLES),
        "found_table_count": len(row_counts),
        "missing_tables": missing_tables,
        "row_counts": row_counts,
        "phase10_gate": {
            "legacy_readonly_snapshot": True,
            "postgresql_schema_approved": False,
            "production_migration_executed": False,
        },
    }


def main():
    """CLI entrypoint for manual Phase 10 readiness checks."""
    parser = argparse.ArgumentParser(description="Phase 10 read-only database snapshot")
    parser.add_argument(
        "--database",
        default=str(DEFAULT_DATABASE),
        help="Path to legacy SQLite database",
    )
    args = parser.parse_args()
    snapshot = snapshot_database(Path(args.database))
    print(json.dumps(snapshot, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
