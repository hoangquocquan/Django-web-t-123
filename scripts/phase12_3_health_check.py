"""Phase 12.3 local health-check runner.

The script checks the local Django migration backend and legacy SQLite database
without changing production systems, routes, or schema.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DJANGO_ROOT = PROJECT_ROOT / "django_backend"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "monitoring" / "health_check_result.json"
DEFAULT_LEGACY_DATABASE = PROJECT_ROOT / "backend" / "database" / "mecprecision.sqlite"

if str(DJANGO_ROOT) not in sys.path:
    sys.path.insert(0, str(DJANGO_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")


def utc_now():
    """Return a timestamp for monitoring evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def elapsed_ms(start):
    """Convert a perf_counter start value to milliseconds."""
    return round((time.perf_counter() - start) * 1000, 4)


def resolve_sqlite_path(database_name):
    """Resolve a Django SQLite NAME value into a filesystem path."""
    text = str(database_name)
    if text.startswith("file:"):
        parsed = urlparse(text)
        return Path(unquote(parsed.path))
    return Path(text)


def make_component(name, status, latency_ms=0.0, details=None):
    """Build one health-check component record."""
    return {
        "name": name,
        "status": status,
        "latency_ms": latency_ms,
        "details": details or {},
    }


def setup_django():
    """Load Django and return the active settings object."""
    start = time.perf_counter()
    import django
    from django.conf import settings

    django.setup()
    if "testserver" not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append("testserver")
    return make_component(
        "application_import",
        "PASS",
        elapsed_ms(start),
        {
            "settings_module": os.environ.get("DJANGO_SETTINGS_MODULE"),
            "debug": bool(settings.DEBUG),
        },
    )


def check_api_endpoint(path):
    """Call one local endpoint through Django test client."""
    from django.test import Client

    client = Client()
    start = time.perf_counter()
    response = client.get(path)
    status = "PASS" if response.status_code < 500 else "FAIL"
    return make_component(
        f"api:{path}",
        status,
        elapsed_ms(start),
        {
            "status_code": response.status_code,
            "available": response.status_code < 500,
        },
    )


def check_database():
    """Verify the legacy SQLite database can be opened read-only."""
    from django.conf import settings

    start = time.perf_counter()
    database_name = settings.DATABASES["legacy"]["NAME"]
    database_path = resolve_sqlite_path(database_name)
    if not database_path.exists() and DEFAULT_LEGACY_DATABASE.exists():
        database_path = DEFAULT_LEGACY_DATABASE
    if not database_path.exists():
        return make_component(
            "database",
            "FAIL",
            elapsed_ms(start),
            {"engine": "SQLite", "path": str(database_path), "error": "database file not found"},
        )

    uri = f"file:{database_path.as_posix()}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as connection:
            integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
            table_count = connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    except sqlite3.Error as exc:
        return make_component(
            "database",
            "FAIL",
            elapsed_ms(start),
            {"engine": "SQLite", "path": str(database_path), "error": str(exc)},
        )

    return make_component(
        "database",
        "PASS" if integrity == "ok" else "FAIL",
        elapsed_ms(start),
        {
            "engine": "SQLite",
            "path": str(database_path),
            "integrity_check": integrity,
            "table_count": table_count,
            "read_only": True,
        },
    )


def check_dependencies():
    """Report configured optional dependencies without connecting to production."""
    start = time.perf_counter()
    dependencies = {
        "redis_url_configured": bool(os.getenv("REDIS_URL")),
        "sentry_dsn_configured": bool(os.getenv("SENTRY_DSN")),
        "ollama_url_configured": bool(os.getenv("OLLAMA_URL")),
        "production_probe_executed": False,
    }
    return make_component("dependencies", "PASS", elapsed_ms(start), dependencies)


def summarize_status(components):
    """Return overall monitoring status from component records."""
    failing = [item for item in components if item["status"] == "FAIL"]
    return "HEALTHY" if not failing else "DEGRADED"


def run_health_check(output_path=None):
    """Run all local monitoring checks and write a JSON result."""
    components = [setup_django()]
    for path in ["/", "/api/health/", "/api/v1/health/"]:
        components.append(check_api_endpoint(path))
    components.append(check_database())
    components.append(check_dependencies())

    result = {
        "phase": "12.3",
        "created_at": utc_now(),
        "environment": "LOCAL_DJANGO_TEST_CLIENT",
        "production_modified": False,
        "routes_changed": False,
        "database_schema_changed": False,
        "component_count": len(components),
        "status": summarize_status(components),
        "components": components,
    }

    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main():
    """Command-line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 12.3 local monitoring health check")
    parser.add_argument("--output", default=None, help="Output JSON path.")
    args = parser.parse_args()

    result = run_health_check(args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "HEALTHY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
