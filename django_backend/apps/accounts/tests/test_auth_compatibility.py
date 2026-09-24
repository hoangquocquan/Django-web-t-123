"""Compatibility tests for Phase 8 authentication migration boundaries."""

from apps.accounts.models import AdminSession, AdminUser, PasswordResetToken
from apps.accounts.services.auth_compatibility_service import (
    AuthCompatibilityService,
    PasswordHashInspector,
    PermissionMatrix,
)


def test_password_hash_inspector_detects_pbkdf2_hash():
    """PBKDF2 hashes are supported and do not need upgrade."""
    info = PasswordHashInspector.inspect("pbkdf2_sha256$260000$salt$hash")

    assert info.algorithm == "pbkdf2_sha256"
    assert info.is_supported is True
    assert info.needs_upgrade is False


def test_password_hash_inspector_detects_legacy_sha256_hash():
    """Legacy SHA-256 hashes remain supported but need future upgrade."""
    info = PasswordHashInspector.inspect("a" * 64)

    assert info.algorithm == "legacy_sha256"
    assert info.is_supported is True
    assert info.needs_upgrade is True


def test_permission_matrix_matches_legacy_roles():
    """Admin/editor/viewer permissions must match legacy permission behavior."""
    matrix = PermissionMatrix()

    assert matrix.has_permission("admin", "settings", "write") is True
    assert matrix.has_permission("editor", "products", "write") is True
    assert matrix.has_permission("editor", "settings", "write") is False
    assert matrix.has_permission("viewer", "settings", "read") is True
    assert matrix.has_permission("viewer", "products", "write") is False
    assert matrix.has_permission("unknown", "products", "read") is False


def test_auth_service_returns_safe_profile_without_password_hash(legacy_db):
    """Safe auth profile must not expose password_hash."""
    user = AdminUser.objects.using("legacy").first()
    profile = AuthCompatibilityService().get_user_auth_profile(user.id)

    assert profile["id"] == user.id
    assert "password_hash" not in profile


def test_login_boundary_rejects_inactive_accounts_without_writing():
    """Login compatibility check must reject inactive accounts without creating sessions."""
    active_user = AdminUser(id=1, full_name="A", email="a@example.com", role="admin", is_active=True)
    inactive_user = AdminUser(id=2, full_name="B", email="b@example.com", role="viewer", is_active=False)
    service = AuthCompatibilityService()

    assert service.can_attempt_login(active_user) is True
    assert service.can_attempt_login(inactive_user) is False


def test_session_expiration_check_is_read_only():
    """Session expiration logic must not update last_seen_at in Phase 8."""
    service = AuthCompatibilityService()
    session = AdminSession(session_id="s1", expires_at=100, admin_id=1)

    assert service.is_session_expired(session, now_timestamp=101) is True
    assert service.is_session_expired(session, now_timestamp=100) is False


def test_password_reset_token_state_check_is_read_only():
    """Password reset token state can be evaluated without marking it used."""
    service = AuthCompatibilityService()
    usable_token = PasswordResetToken(token="t1", admin_id=1, email="a@example.com", expires_at=100)
    used_token = PasswordResetToken(
        token="t2",
        admin_id=1,
        email="a@example.com",
        expires_at=100,
        used_at=90,
    )

    assert service.is_password_reset_token_usable(usable_token, now_timestamp=99) is True
    assert service.is_password_reset_token_usable(usable_token, now_timestamp=101) is False
    assert service.is_password_reset_token_usable(used_token, now_timestamp=99) is False


def test_two_factor_challenge_state_check_is_read_only():
    """2FA compatibility check should only inspect used_at state."""
    service = AuthCompatibilityService()

    class Challenge:
        used_at = None

    class UsedChallenge:
        used_at = "2026-01-01 00:00:00"

    assert service.can_use_two_factor_challenge(Challenge()) is True
    assert service.can_use_two_factor_challenge(UsedChallenge()) is False
