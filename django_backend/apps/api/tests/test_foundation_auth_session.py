"""Regression tests for the Foundation authentication session endpoints."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.foundation.models import FoundationAuthToken, FoundationRole, FoundationUser
from apps.foundation.services import FoundationAuthService


def _session(*, suffix="sales"):
    role = FoundationRole.objects.create(name=f"Session {suffix}")
    user = FoundationUser.objects.create(
        email=f"{suffix}@session.invalid",
        full_name=f"Session {suffix}",
        password_hash="test-only",
        role=role,
    )
    raw_token = f"session-{suffix}-token"
    token = FoundationAuthToken.objects.create(
        user=user,
        token_hash=FoundationAuthService.hash_token(raw_token),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    return raw_token, token


def _auth(raw_token):
    return {"HTTP_AUTHORIZATION": f"Bearer {raw_token}"}


@pytest.mark.django_db
def test_logout_revokes_callers_token_without_auth_read_permission(client):
    """Every authenticated role may revoke its own session token."""
    raw_token, token = _session()

    response = client.post("/api/v1/foundation/auth/logout/", **_auth(raw_token))

    assert response.status_code == 200, response.json()
    assert response.json() == {"success": True, "data": {"logged_out": True}}
    token.refresh_from_db()
    assert token.revoked_at is not None

    rejected = client.post("/api/v1/foundation/auth/logout/", **_auth(raw_token))
    assert rejected.status_code == 401


@pytest.mark.django_db
def test_logout_only_revokes_the_presented_token(client):
    first_raw, first_token = _session(suffix="first")
    _second_raw, second_token = _session(suffix="second")

    response = client.post("/api/v1/foundation/auth/logout/", **_auth(first_raw))

    assert response.status_code == 200, response.json()
    first_token.refresh_from_db()
    second_token.refresh_from_db()
    assert first_token.revoked_at is not None
    assert second_token.revoked_at is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("authorization", "expected_status"),
    [
        (None, 403),
        ("Token wrong-scheme", 401),
        ("Bearer invalid-token", 401),
    ],
)
def test_logout_rejects_missing_malformed_or_unknown_credentials(
    client, authorization, expected_status
):
    _raw_token, token = _session(suffix="protected")
    headers = {} if authorization is None else {"HTTP_AUTHORIZATION": authorization}

    response = client.post("/api/v1/foundation/auth/logout/", **headers)

    assert response.status_code == expected_status
    token.refresh_from_db()
    assert token.revoked_at is None
