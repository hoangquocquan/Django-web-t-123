import sqlite3

import pytest

from apps.accounts.models import AdminUser
from apps.accounts.repositories.auth_repository import AdminUserRepository
from apps.foundation.models import FoundationPermission, FoundationRole, FoundationUser
from apps.foundation.services import (
    FoundationAuthService,
    FoundationPermissionService,
    FoundationUserService,
)
from scripts.copy_legacy_database_for_test import copy_legacy_database


@pytest.fixture
def legacy_db(tmp_path):
    """Return a read-only copied legacy database path for compatibility checks."""
    return copy_legacy_database(
        destination=tmp_path / "legacy_database" / "mecprecision-test.sqlite"
    )


def count_legacy_rows(legacy_db, table_name):
    """Count legacy rows without using Django writes or migrations."""
    connection_uri = f"file:{legacy_db.as_posix()}?mode=ro"
    with sqlite3.connect(connection_uri, uri=True) as legacy_connection:
        return legacy_connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


@pytest.fixture
def foundation_user():
    """Create a login-capable Django-owned user for API tests."""
    service = FoundationUserService()
    return service.create_user(
        email="foundation-user@example.com",
        full_name="Foundation User",
        password="SecurePass123!",
        role_name="admin",
        profile={"phone": "0900000000"},
    )


def bearer_header(user):
    """Create an Authorization header for a Django-owned user."""
    token, _token_row = FoundationAuthService().login(user.email, "SecurePass123!")
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.mark.django_db
def test_foundation_migrations_seed_roles_permissions_and_legacy_users():
    assert FoundationRole.objects.filter(name__in=["admin", "editor", "viewer"]).count() == 3
    assert FoundationPermission.objects.filter(code="*:*").exists()
    assert FoundationPermission.objects.filter(code="*:read").exists()
    assert FoundationUser.objects.filter(legacy_admin_id__isnull=False).count() >= 1


@pytest.mark.django_db
def test_foundation_user_service_creates_user_and_profile():
    user = FoundationUserService().create_user(
        email="new-foundation@example.com",
        full_name="New Foundation",
        password="SecurePass123!",
        role_name="viewer",
        profile={"avatar_url": "/media/avatar.png", "language": "vi"},
    )

    assert user.id
    assert user.role.name == "viewer"
    assert user.profile.avatar_url == "/media/avatar.png"
    assert user.profile.language == "vi"


@pytest.mark.django_db
def test_foundation_auth_service_login_authenticate_and_logout(foundation_user):
    auth_service = FoundationAuthService()

    raw_token, token = auth_service.login(foundation_user.email, "SecurePass123!")
    authenticated_user = auth_service.authenticate_token(raw_token)

    assert token.id
    assert authenticated_user.email == foundation_user.email
    assert auth_service.logout(raw_token) is True

    with pytest.raises(Exception):
        auth_service.authenticate_token(raw_token)


@pytest.mark.django_db
def test_foundation_permission_service_uses_django_roles(foundation_user):
    permission_service = FoundationPermissionService()

    assert permission_service.has_permission(foundation_user, "users", "write") is True
    assert permission_service.has_permission(foundation_user, "products", "read") is True


@pytest.mark.django_db
def test_foundation_login_api_returns_token(client, foundation_user):
    response = client.post(
        "/api/v1/foundation/auth/login/",
        data={"email": foundation_user.email, "password": "SecurePass123!"},
        content_type="application/json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["token"]
    assert body["data"]["user"]["email"] == foundation_user.email


@pytest.mark.django_db
def test_foundation_user_api_allows_admin_create_and_list(client, foundation_user):
    headers = bearer_header(foundation_user)

    create_response = client.post(
        "/api/v1/foundation/users/",
        data={
            "email": "api-created-user@example.com",
            "full_name": "API Created User",
            "password": "SecurePass123!",
            "role": "viewer",
            "phone": "0900111222",
        },
        content_type="application/json",
        **headers,
    )
    list_response = client.get("/api/v1/foundation/users/", **headers)

    assert create_response.status_code == 201
    assert create_response.json()["data"]["email"] == "api-created-user@example.com"
    assert list_response.status_code == 200
    emails = [item["email"] for item in list_response.json()["data"]["results"]]
    assert "api-created-user@example.com" in emails


@pytest.mark.django_db
def test_foundation_profile_api_updates_profile(client, foundation_user):
    response = client.put(
        f"/api/v1/foundation/users/{foundation_user.id}/profile/",
        data={"phone": "0911222333", "language": "en"},
        content_type="application/json",
        **bearer_header(foundation_user),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["profile"]["phone"] == "0911222333"
    assert body["data"]["profile"]["language"] == "en"


@pytest.mark.django_db
def test_foundation_permission_apis_return_django_permission_data(client, foundation_user):
    headers = bearer_header(foundation_user)
    roles_response = client.get("/api/v1/foundation/permissions/roles/", **headers)
    check_response = client.post(
        "/api/v1/foundation/permissions/check/",
        data={"module": "users", "action": "write"},
        content_type="application/json",
        **headers,
    )

    assert roles_response.status_code == 200
    assert any(role["name"] == "admin" for role in roles_response.json()["data"])
    assert check_response.status_code == 200
    assert check_response.json()["data"]["allowed"] is True


@pytest.mark.django_db
def test_foundation_api_rejects_missing_token(client):
    response = client.get("/api/v1/foundation/users/")

    assert response.status_code == 403
    assert response.json()["success"] is False


@pytest.mark.django_db
def test_legacy_auth_compatibility_remains_read_only(legacy_db):
    assert AdminUser._meta.managed is False
    assert AdminUserRepository().list_users()._db == "legacy"
    assert count_legacy_rows(legacy_db, "admin_users") >= 1

    legacy_user = AdminUser(
        id=999,
        full_name="Legacy User",
        email="legacy@example.com",
        password_hash="not-exposed",
        role="viewer",
        is_active=True,
        created_at="2026-01-01 00:00:00",
    )
    with pytest.raises(RuntimeError):
        legacy_user.save()
