"""Deterministic checks for PROD-02 production configuration."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from apps.core import api_compatibility

ROOT = Path(__file__).resolve().parents[1]


def run_production_settings(overrides=None):
    """Import production settings in an isolated process with a clean contract."""
    environment = os.environ.copy()
    for key in ("SECRET_KEY", "ALLOWED_HOSTS", "DATABASE_URL", "REDIS_URL"):
        environment.pop(key, None)
    environment.update(overrides or {})
    settings_probe = (
        "import config.settings.production as s; "
        "print(s.DEBUG, s.DATABASES['default']['ENGINE'], "
        "s.CACHES['default']['BACKEND'])"
    )
    return subprocess.run(
        [
            sys.executable,
            "-c",
            settings_probe,
        ],
        cwd=ROOT / "django_backend",
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )


def valid_environment():
    """Return non-secret, test-only values for isolated settings validation."""
    return {
        "SECRET_KEY": "prod02-test-key-not-for-runtime",
        "ALLOWED_HOSTS": "example.test",
        "DATABASE_URL": "postgresql://user:password@database:5432/mecprecision",
        "REDIS_URL": "redis://:password@redis:6379/0",
    }


def test_production_settings_fail_fast_for_each_required_value():
    for missing in ("SECRET_KEY", "ALLOWED_HOSTS", "DATABASE_URL", "REDIS_URL"):
        environment = valid_environment()
        environment.pop(missing)
        result = run_production_settings(environment)
        assert result.returncode != 0
        assert missing in result.stderr


def test_production_settings_require_postgres_and_redis_schemes():
    environment = valid_environment()
    environment["DATABASE_URL"] = "sqlite:///unsafe.sqlite3"
    assert run_production_settings(environment).returncode != 0

    environment = valid_environment()
    environment["REDIS_URL"] = "http://redis:6379"
    assert run_production_settings(environment).returncode != 0


def test_valid_production_settings_are_secure_and_use_real_services():
    result = run_production_settings(valid_environment())
    assert result.returncode == 0, result.stderr
    assert "False django.db.backends.postgresql" in result.stdout
    assert "django.core.cache.backends.redis.RedisCache" in result.stdout


def test_container_uses_gunicorn_non_root_and_excludes_runtime_artifacts():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")

    assert "config.settings.production" in dockerfile
    assert "gunicorn" in dockerfile
    assert "runserver" not in dockerfile
    assert "USER appuser" in dockerfile
    assert "requirements-prod.txt" in dockerfile
    assert "requirements.txt /tmp/django-requirements.txt" not in dockerfile
    for pattern in (
        "*.zip",
        "*.sqlite",
        "*.db",
        "**/*.zip",
        "**/*.sqlite3",
        "**/*.db",
        "backups/",
    ):
        assert pattern in dockerignore

    production = (ROOT / "django_backend/config/settings/production.py").read_text(
        encoding="utf-8"
    )
    assert "WhiteNoiseMiddleware" in production
    assert "CompressedManifestStaticFilesStorage" in production


def test_compose_requires_secrets_and_private_postgres_redis():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "config.settings.production" in compose
    assert "POSTGRES_PASSWORD:?" in compose
    assert "REDIS_PASSWORD:?" in compose
    assert "postgresql://" in compose
    assert "redis://:" in compose
    assert '"5432:5432"' not in compose
    assert '"6379:6379"' not in compose


def test_production_health_uses_django_database_and_cache(monkeypatch, settings):
    """Production health must not report the removed legacy SQLite file."""
    settings.ENVIRONMENT = "production"
    monkeypatch.setattr(
        api_compatibility, "is_default_database_available", lambda: True
    )
    monkeypatch.setattr(api_compatibility, "is_default_cache_available", lambda: True)
    monkeypatch.setattr(
        api_compatibility, "is_legacy_database_available", lambda: False
    )

    result = api_compatibility.build_legacy_health_response()

    assert result["status"] == "ok"
    assert result["environment"] == "production"
    assert result["database"] == "ok"
    assert result["redis_enabled"] is True
