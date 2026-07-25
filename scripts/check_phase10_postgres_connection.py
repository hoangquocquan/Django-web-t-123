"""Validate the PostgreSQL dry-run target for Phase 10.2.1.

The script is intentionally defensive. It refuses production-looking database
names before attempting any network connection, then checks PostgreSQL version
and permissions only when the URL is structurally safe.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is installed in Django env.
    load_dotenv = None


ENV_NAME = "PHASE10_DRY_RUN_DATABASE_URL"
SAFE_DATABASE_NAME_MARKERS = {"test", "dryrun", "dry_run", "staging", "dev"}
FORBIDDEN_DATABASE_NAME_MARKERS = {"prod", "production", "live"}
SYSTEM_DATABASE_NAMES = {"postgres", "template0", "template1"}


def load_dryrun_environment():
    """Load local dry-run env files without requiring them to exist."""
    if load_dotenv is None:
        return

    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env", override=False)
    load_dotenv(project_root / ".env.dryrun", override=False)


def mask_database_url(database_url):
    """Hide passwords before printing database URLs in logs or reports."""
    if not database_url:
        return ""

    parsed = urlparse(database_url)
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    username = parsed.username or ""
    auth = f"{username}:***@" if username else ""
    return f"{parsed.scheme}://{auth}{host}{port}{parsed.path}"


def database_name_from_url(database_url):
    """Return the database name part of a PostgreSQL URL."""
    return urlparse(database_url).path.lstrip("/")


def database_name_tokens(database_name):
    """Split a database name into readable safety tokens."""
    normalized = database_name.lower()
    tokens = {token for token in re.split(r"[^a-z0-9]+", normalized) if token}
    tokens.add(normalized)
    return tokens


def is_postgresql_url(database_url):
    """Return True when the URL scheme is postgres/postgresql."""
    return urlparse(database_url).scheme in {"postgres", "postgresql"}


def is_safe_test_database_url(database_url):
    """Allow only database names that clearly mark a non-production target."""
    database_name = database_name_from_url(database_url).lower()
    return any(marker in database_name for marker in SAFE_DATABASE_NAME_MARKERS)


def has_forbidden_database_name(database_url):
    """Reject database names that look like production/live databases."""
    database_name = database_name_from_url(database_url).lower()
    tokens = database_name_tokens(database_name)
    return (
        database_name in SYSTEM_DATABASE_NAMES
        or bool(tokens.intersection(FORBIDDEN_DATABASE_NAME_MARKERS))
    )


def validate_dryrun_database_url(database_url):
    """Validate URL format and non-production naming before connecting."""
    errors = []
    warnings = []
    database_name = database_name_from_url(database_url) if database_url else ""

    if not database_url:
        errors.append(f"{ENV_NAME} is not configured.")
    elif not is_postgresql_url(database_url):
        errors.append("Dry-run target must use postgres/postgresql URL scheme.")
    elif not database_name:
        errors.append("Dry-run database URL must include a database name.")
    else:
        if has_forbidden_database_name(database_url):
            errors.append(
                "Dry-run database name looks like production/live/system database."
            )
        if not is_safe_test_database_url(database_url):
            errors.append(
                "Dry-run database name must include test, dryrun, dry_run, staging or dev."
            )

    if database_url and urlparse(database_url).password in {"password", "change-me"}:
        warnings.append("Database URL still contains an example password.")

    return {
        "database_name": database_name,
        "masked_database_url": mask_database_url(database_url),
        "is_postgresql_url": bool(database_url and is_postgresql_url(database_url)),
        "is_safe_non_production_name": bool(
            database_url and is_safe_test_database_url(database_url)
        ),
        "has_forbidden_database_name": bool(
            database_url and has_forbidden_database_name(database_url)
        ),
        "errors": errors,
        "warnings": warnings,
    }


def check_postgres_connection(database_url):
    """Connect to PostgreSQL and verify version plus minimum dry-run permissions."""
    result = {
        "connection_checked": False,
        "connection_ok": False,
        "postgresql_version": "",
        "current_database": "",
        "current_user": "",
        "permissions": {},
        "errors": [],
    }

    validation = validate_dryrun_database_url(database_url)
    if validation["errors"]:
        result["errors"].extend(validation["errors"])
        return result

    try:
        import psycopg
    except ImportError:
        result["errors"].append("psycopg is not installed.")
        return result

    result["connection_checked"] = True
    try:
        with psycopg.connect(database_url, connect_timeout=5) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SHOW server_version")
                result["postgresql_version"] = cursor.fetchone()[0]

                cursor.execute("SELECT current_database(), current_user")
                current_database, current_user = cursor.fetchone()
                result["current_database"] = current_database
                result["current_user"] = current_user

                permission_queries = {
                    "database_connect": "SELECT has_database_privilege(current_database(), 'CONNECT')",
                    "database_temp": "SELECT has_database_privilege(current_database(), 'TEMP')",
                    "public_schema_usage": "SELECT has_schema_privilege('public', 'USAGE')",
                    "public_schema_create": "SELECT has_schema_privilege('public', 'CREATE')",
                }
                for permission_name, query in permission_queries.items():
                    cursor.execute(query)
                    result["permissions"][permission_name] = bool(cursor.fetchone()[0])

        missing_permissions = [
            name for name, allowed in result["permissions"].items() if not allowed
        ]
        if missing_permissions:
            result["errors"].append(
                "Dry-run user is missing required permissions: "
                + ", ".join(missing_permissions)
            )
        else:
            result["connection_ok"] = True
    except Exception as exc:  # pragma: no cover - depends on local PostgreSQL.
        result["errors"].append(f"PostgreSQL connection failed: {exc}")

    return result


def evaluate_postgres_environment(database_url=None, check_connection=True):
    """Build a structured environment report for docs and CI output."""
    load_dryrun_environment()
    database_url = database_url or os.getenv(ENV_NAME, "")
    validation = validate_dryrun_database_url(database_url)
    connection = (
        check_postgres_connection(database_url)
        if database_url and not validation["errors"] and check_connection
        else {
            "connection_checked": False,
            "connection_ok": False,
            "postgresql_version": "",
            "current_database": "",
            "current_user": "",
            "permissions": {},
            "errors": [],
        }
    )

    errors = validation["errors"] + connection["errors"]
    if not database_url:
        status = "not_configured"
    elif errors:
        status = "blocked"
    elif check_connection and connection["connection_ok"]:
        status = "ready"
    else:
        status = "validated_without_connection"

    return {
        "status": status,
        "safe_to_proceed": status == "ready",
        "production_touched": False,
        "validation": validation,
        "connection": connection,
        "errors": errors,
        "warnings": validation["warnings"],
    }


def main():
    """CLI entrypoint for PostgreSQL dry-run environment validation."""
    parser = argparse.ArgumentParser(
        description="Validate Phase 10 PostgreSQL dry-run connection"
    )
    parser.add_argument("--database-url", default=None, help="Override dry-run URL")
    parser.add_argument(
        "--skip-connection",
        action="store_true",
        help="Only validate URL and safety naming; do not connect to PostgreSQL",
    )
    args = parser.parse_args()

    result = evaluate_postgres_environment(
        args.database_url,
        check_connection=not args.skip_connection,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result["status"] in {"not_configured", "validated_without_connection"}:
        return 0
    return 0 if result["safe_to_proceed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
