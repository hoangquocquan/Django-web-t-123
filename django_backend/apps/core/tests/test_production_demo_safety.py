"""Safety regression tests for the synthetic local demo tooling."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from apps.core.production_demo_seed.ownership import SAFE_EMAIL_DOMAIN
from apps.core.production_demo_seed.safety import allow_database, allow_environment
from apps.foundation.models import FoundationPermission, FoundationRole, FoundationUser
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test.utils import override_settings


@pytest.fixture
def allowed_demo_settings(settings):
    settings.DEMO_TOOLING_ENVIRONMENT = "TEST"
    settings.DEMO_TOOLING_DATABASE_ALLOWLIST = [
        {
            "engine": "sqlite",
            "path": settings.DATABASES["default"]["NAME"],
            "non_production": True,
        }
    ]
    return settings


@pytest.mark.django_db
@pytest.mark.parametrize("environment", ["DEV", "TEST", "STAGING", "UAT"])
def test_allowlisted_environments_are_explicitly_allowed(allowed_demo_settings, environment):
    allowed_demo_settings.DEMO_TOOLING_ENVIRONMENT = environment
    assert allow_environment() is True


@pytest.mark.django_db
@pytest.mark.parametrize("environment", ["", "UNKNOWN", "PRODUCTION", "true"])
def test_unknown_or_production_environment_is_denied(allowed_demo_settings, environment):
    allowed_demo_settings.DEMO_TOOLING_ENVIRONMENT = environment
    assert allow_environment() is False


@pytest.mark.django_db
def test_database_requires_exact_allowlist_and_does_not_treat_sqlite_as_safe(settings):
    settings.DEMO_TOOLING_ENVIRONMENT = "TEST"
    settings.DEMO_TOOLING_DATABASE_ALLOWLIST = []
    assert allow_database() is False


@pytest.mark.django_db
def test_unknown_remote_database_is_denied_even_when_name_matches(settings):
    databases = dict(settings.DATABASES)
    databases["default"] = {
        **settings.DATABASES["default"],
        "ENGINE": "django.db.backends.postgresql",
        "HOST": "unknown.internal.example",
        "PORT": "5432",
        "NAME": "staging_db",
    }
    with override_settings(
        DATABASES=databases,
        DEMO_TOOLING_ENVIRONMENT="STAGING",
        DEMO_TOOLING_DATABASE_ALLOWLIST=[
            {
                "engine": "postgresql",
                "host": "unknown.internal.example",
                "port": "5432",
                "name": "staging_db",
            }
        ],
    ):
        assert allow_database() is False


@pytest.mark.django_db
def test_production_sqlite_path_is_denied_when_not_allowlisted(settings, tmp_path):
    db_path = str(tmp_path / "production.sqlite3")
    databases = dict(settings.DATABASES)
    databases["default"] = {**settings.DATABASES["default"], "NAME": db_path}
    with override_settings(
        DEMO_TOOLING_ENVIRONMENT="PRODUCTION",
        DATABASES=databases,
        DEMO_TOOLING_DATABASE_ALLOWLIST=[{"engine": "sqlite", "path": db_path}],
    ):
        assert allow_environment() is False
        assert allow_database() is False


@pytest.mark.django_db
def test_full_profile_refuses_before_write(allowed_demo_settings):
    with pytest.raises(ValueError, match="FULL is disabled"):
        call_command("seed_production_demo", "--profile", "FULL", "--dry-run")


@pytest.mark.django_db
def test_demo_user_requires_reserved_domain_and_allowed_database(allowed_demo_settings, monkeypatch):
    role = FoundationRole.objects.create(name="DemoSales", is_active=True)
    FoundationPermission.objects.get_or_create(
        code="sales:read", defaults={"module": "sales", "action": "read"}
    )[0].roles.add(role)
    monkeypatch.setenv("MEC_AI_DEMO_PASSWORD", "OperatorOnly-123!")
    with pytest.raises(CommandError, match=f"@{SAFE_EMAIL_DOMAIN}"):
        call_command("ensure_local_ai_demo_user", "--email", "real@example.com", stdout=io.StringIO())


@pytest.mark.django_db
def test_existing_non_demo_user_collision_fails_closed(allowed_demo_settings, monkeypatch):
    role = FoundationRole.objects.create(name="DemoSales", is_active=True)
    FoundationPermission.objects.get_or_create(
        code="sales:read", defaults={"module": "sales", "action": "read"}
    )[0].roles.add(role)
    email = f"owned@{SAFE_EMAIL_DOMAIN}"
    FoundationUser.objects.create(
        email=email,
        full_name="Existing unrelated user",
        password_hash="unchanged",
        role=role,
    )
    monkeypatch.setenv("MEC_AI_DEMO_PASSWORD", "OperatorOnly-123!")
    with pytest.raises(CommandError, match="collision"):
        call_command("ensure_local_ai_demo_user", "--email", email, stdout=io.StringIO())
    assert FoundationUser.objects.get(email=email).password_hash == "unchanged"


@pytest.mark.django_db
def test_owned_demo_user_is_idempotent(allowed_demo_settings, monkeypatch):
    role = FoundationRole.objects.create(name="DemoSales", is_active=True)
    FoundationPermission.objects.get_or_create(
        code="sales:read", defaults={"module": "sales", "action": "read"}
    )[0].roles.add(role)
    email = f"owned@{SAFE_EMAIL_DOMAIN}"
    monkeypatch.setenv("MEC_AI_DEMO_PASSWORD", "OperatorOnly-123!")
    call_command("ensure_local_ai_demo_user", "--email", email, "--role", "DemoSales", stdout=io.StringIO())
    first = FoundationUser.objects.get(email=email)
    call_command("ensure_local_ai_demo_user", "--email", email, "--role", "DemoSales", stdout=io.StringIO())
    assert FoundationUser.objects.filter(email=email).count() == 1
    assert FoundationUser.objects.get(email=email).role_id == first.role_id


def test_seed_package_has_no_external_provider_or_destructive_calls():
    root = Path(__file__).resolve().parents[1] / "production_demo_seed"
    source = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    forbidden = (
        "api.line.me",
        "n8n",
        "requests.",
        "httpx",
        "send_mail",
        "truncate(",
        "flush(",
        "drop_table",
    )
    assert not any(marker in source for marker in forbidden)
