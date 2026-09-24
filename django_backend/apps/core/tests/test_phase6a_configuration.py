"""Phase 6A production-like settings and readiness tests."""

import os
import subprocess
import sys

import pytest

from apps.core import views

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
BASE_ENV = {
    "DJANGO_SETTINGS_MODULE": "config.settings.production",
    "SECRET_KEY": "fictional-phase6-test-key",
    "ALLOWED_HOSTS": "localhost,127.0.0.1",
    "DATABASE_URL": "postgresql://fictional:fictional@127.0.0.1:5432/fictional",
    "REDIS_URL": "redis://:fictional@127.0.0.1:6379/0",
    "METRICS_BEARER_TOKEN": "fictional-metrics-token",
    "CORS_ALLOWED_ORIGINS": "",
    "CSRF_TRUSTED_ORIGINS": "https://localhost",
}


def _import_settings(changes=None, module="config.settings.production"):
    environment = os.environ.copy()
    environment.update(BASE_ENV)
    environment["DJANGO_SETTINGS_MODULE"] = module
    environment.update(changes or {})
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "from django.conf import settings; print(settings.DEBUG)",
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"DATABASE_URL": "sqlite:///unsafe.sqlite3"}, "service URL"),
        ({"DATABASE_URL": "postgresql://127.0.0.1"}, "service URL"),
        ({"REDIS_URL": "http://127.0.0.1:6379"}, "service URL"),
        ({"REDIS_URL": "redis://127.0.0.1:6379/0"}, "service URL"),
        ({"ALLOWED_HOSTS": "*"}, "explicit host names"),
        ({"ALLOWED_HOSTS": ""}, "must contain at least one host"),
        ({"CORS_ALLOWED_ORIGINS": "https://remote.invalid"}, "must be empty"),
        ({"CSRF_TRUSTED_ORIGINS": "https://*.invalid"}, "explicit HTTP(S) origins"),
        ({"SECRET_KEY": "CHANGE_ME"}, "unsafe placeholder"),
    ],
)
def test_production_settings_fail_closed(changes, message):
    result = _import_settings(changes)
    assert result.returncode != 0
    assert message in result.stderr


def test_production_security_defaults_and_same_origin_policy():
    code = (
        "from django.conf import settings as s; "
        "assert s.DEBUG is False; assert s.CORS_ALLOWED_ORIGINS == []; "
        "assert s.SESSION_COOKIE_SECURE and s.SESSION_COOKIE_HTTPONLY; "
        "assert s.SESSION_COOKIE_SAMESITE == 'Lax'; "
        "assert s.CSRF_COOKIE_SECURE and s.CSRF_COOKIE_HTTPONLY"
    )
    environment = os.environ.copy()
    environment.update(BASE_ENV)
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_development_origin_is_environment_based_and_loopback_only():
    allowed = _import_settings(
        {"CORS_ALLOWED_ORIGINS": "http://127.0.0.1:8443"},
        "config.settings.development",
    )
    denied = _import_settings(
        {"CORS_ALLOWED_ORIGINS": "https://remote.invalid"},
        "config.settings.development",
    )
    assert allowed.returncode == 0, allowed.stderr
    assert denied.returncode != 0
    assert "loopback HTTP origins" in denied.stderr


@pytest.mark.django_db
def test_liveness_does_not_touch_dependencies_but_readiness_does(client, monkeypatch):
    monkeypatch.setattr(
        views.cache,
        "set",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("down")),
    )
    assert client.get("/api/v1/phase6/live/").status_code == 200
    response = client.get("/api/v1/phase6/ready/")
    assert response.status_code == 503
    assert response.json() == {"success": False, "data": {"status": "not_ready"}}
