"""Validation tests for Phase 8 read-only auth ORM mappings."""

from django.db import connections
import pytest

from apps.accounts.models import (
    AdminActivityLog,
    AdminSession,
    AdminTwoFactorChallenge,
    AdminUser,
    LoginAttempt,
    PasswordResetToken,
)
from apps.accounts.repositories.auth_repository import (
    AdminActivityLogRepository,
    AdminSessionRepository,
    AdminUserRepository,
    LoginAttemptRepository,
    PasswordResetTokenRepository,
    TwoFactorChallengeRepository,
)


def table_count(table_name):
    """Count rows directly in a legacy table for ORM parity checks."""
    with connections["legacy"].cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]


@pytest.mark.parametrize(
    ("model", "table_name"),
    [
        (AdminUser, "admin_users"),
        (AdminSession, "admin_sessions"),
        (LoginAttempt, "login_attempts"),
        (PasswordResetToken, "password_reset_tokens"),
        (AdminTwoFactorChallenge, "admin_2fa_challenges"),
        (AdminActivityLog, "admin_activity_logs"),
    ],
)
def test_auth_model_table_mapping_matches_legacy_count(legacy_db, model, table_name):
    """Auth unmanaged models must map to legacy auth tables."""
    assert model.objects.using("legacy").count() == table_count(table_name)


def test_admin_session_relationship_resolves(legacy_db):
    """AdminSession -> AdminUser foreign key resolves through legacy alias."""
    session = AdminSession.objects.using("legacy").select_related("admin").first()

    assert session is not None
    assert session.admin_id == session.admin.id
    assert session.email == session.admin.email


def test_password_reset_token_relationship_resolves(legacy_db):
    """PasswordResetToken -> AdminUser foreign key resolves when token data exists."""
    token = PasswordResetToken.objects.using("legacy").select_related("admin").first()

    assert token is not None
    assert token.admin_id == token.admin.id


def test_auth_tables_do_not_have_orphan_admin_references(legacy_db):
    """Auth child tables must not point to missing admin users."""
    checks = [
        ("admin_sessions", "admin_id"),
        ("password_reset_tokens", "admin_id"),
        ("admin_2fa_challenges", "admin_id"),
        ("admin_activity_logs", "admin_id"),
    ]
    with connections["legacy"].cursor() as cursor:
        for table_name, column_name in checks:
            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM {table_name} child
                LEFT JOIN admin_users users ON users.id = child.{column_name}
                WHERE child.{column_name} IS NOT NULL AND users.id IS NULL
                """
            )
            assert cursor.fetchone()[0] == 0


def test_auth_repositories_read_from_legacy_database(legacy_db):
    """Auth repositories must create QuerySets on alias `legacy`."""
    assert AdminUserRepository().list_users()._db == "legacy"
    assert AdminSessionRepository().list_sessions()._db == "legacy"
    assert LoginAttemptRepository().list_attempts()._db == "legacy"
    assert PasswordResetTokenRepository().list_tokens()._db == "legacy"
    assert TwoFactorChallengeRepository().list_challenges()._db == "legacy"
    assert AdminActivityLogRepository().list_activity_logs()._db == "legacy"


def test_admin_user_repository_defers_password_hash_by_default(legacy_db):
    """Default admin user reads must not select password_hash."""
    user = AdminUserRepository().list_users().first()

    assert "password_hash" in user.get_deferred_fields()


def test_auth_models_block_instance_save_and_delete(legacy_db):
    """Auth legacy models reject accidental instance writes."""
    user = AdminUser.objects.using("legacy").first()

    with pytest.raises(RuntimeError):
        user.save()

    with pytest.raises(RuntimeError):
        user.delete()


def test_auth_models_block_bulk_update_and_delete(legacy_db):
    """Auth legacy querysets reject accidental bulk writes."""
    queryset = AdminUser.objects.using("legacy").filter(role="viewer")

    with pytest.raises(RuntimeError):
        queryset.update(role="admin")

    with pytest.raises(RuntimeError):
        queryset.delete()
