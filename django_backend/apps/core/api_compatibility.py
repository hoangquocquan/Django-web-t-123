"""Compatibility helpers for the first controlled API cutover.

Phase 9 intentionally starts with the lowest-risk endpoint: health check.
This module keeps the response compatible with the legacy `/api/health`
contract while Django begins serving the route.
"""

import os
import sqlite3
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.core.cache import cache
from django.db import connections

LEGACY_HEALTH_ENDPOINT = "/api/health"
DJANGO_HEALTH_ENDPOINT = "/api/v1/health"
ROLLBACK_STATUS_ENDPOINT = "/api/v1/cutover/health/rollback"
LEGACY_API_VERSION = "1.1.0"


def _env_bool(name, default=False):
    """Read a legacy-style boolean environment variable safely."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _legacy_database_path():
    """Convert the configured legacy database URI into a local file path.

    Django opens the legacy SQLite database in read-only URI mode. For the
    health check we only need to verify that the file exists; no SQL query is
    executed and no schema is modified.
    """
    legacy_config = settings.DATABASES.get("legacy", {})
    database_name = str(legacy_config.get("NAME", ""))
    if not database_name:
        return None

    if database_name.startswith("file:"):
        parsed = urlparse(database_name)
        path = unquote(parsed.path)
        if len(path) > 2 and path[0] == "/" and path[2] == ":":
            path = path[1:]
        return Path(path)

    return Path(database_name)


def is_legacy_database_available():
    """Return True when the legacy SQLite file configured for Django exists."""
    database_path = _legacy_database_path()
    return bool(database_path and database_path.exists())


def is_default_database_available():
    """Probe the Django-owned database without leaking connection details."""
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            return cursor.fetchone() == (1,)
    except Exception:  # noqa: BLE001 - health must degrade instead of exposing internals
        return False


def is_default_cache_available():
    """Probe the configured cache using a short-lived non-sensitive value."""
    try:
        key = "health:cache"
        cache.set(key, "ok", timeout=5)
        return cache.get(key) == "ok"
    except Exception:  # noqa: BLE001 - health must degrade instead of exposing internals
        return False


def build_legacy_health_response():
    """Build the same public health payload shape used by legacy backend.

    This function is the compatibility adapter. If an old client expects
    `status`, `api_version`, `database`, or `redis_enabled`, it can continue
    reading those keys after the route is served by Django.
    """
    production_runtime = getattr(settings, "ENVIRONMENT", "development") == "production"
    database_ok = (
        is_default_database_available()
        if production_runtime
        else is_legacy_database_available()
    )
    redis_enabled = (
        is_default_cache_available()
        if production_runtime
        else _env_bool("MEC_REDIS_CACHE_ENABLED", False)
    )
    return {
        "status": "ok"
        if database_ok and (redis_enabled or not production_runtime)
        else "degraded",
        "api_version": LEGACY_API_VERSION,
        "environment": getattr(
            settings, "ENVIRONMENT", os.getenv("MEC_ENV", "development")
        ),
        "database": "ok" if database_ok else "missing",
        "sqlite_version": sqlite3.sqlite_version,
        "redis_enabled": redis_enabled,
    }


def build_cutover_status_response():
    """Describe which endpoint has been cut over and how it is protected."""
    return {
        "success": True,
        "phase": 9,
        "cutover": {
            "endpoint": LEGACY_HEALTH_ENDPOINT,
            "django_endpoint": DJANGO_HEALTH_ENDPOINT,
            "legacy_endpoint": LEGACY_HEALTH_ENDPOINT,
            "status": "enabled",
            "type": "read_only_health_check",
        },
        "compatibility_contract": {
            "preserved_keys": [
                "status",
                "api_version",
                "environment",
                "database",
                "sqlite_version",
                "redis_enabled",
            ],
            "write_api_cutover": False,
            "auth_cutover": False,
        },
        "rollback": {
            "status_endpoint": ROLLBACK_STATUS_ENDPOINT,
            "strategy": "route /api/health back to legacy backend if contract tests fail",
        },
    }


def build_health_rollback_response():
    """Return rollback instructions without mutating runtime configuration."""
    return {
        "success": True,
        "phase": 9,
        "rollback_ready": True,
        "endpoint": LEGACY_HEALTH_ENDPOINT,
        "actions": [
            "remove Django route/proxy rule for /api/health",
            "restore legacy backend route /api/health as the active target",
            "run health contract tests again",
        ],
        "safety": {
            "database_changed": False,
            "legacy_code_changed": False,
            "write_api_cutover": False,
        },
    }
