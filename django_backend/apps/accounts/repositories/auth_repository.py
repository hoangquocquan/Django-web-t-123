"""Read-only repository adapter for legacy authentication data."""

from apps.accounts.models import (
    AdminActivityLog,
    AdminSession,
    AdminTwoFactorChallenge,
    AdminUser,
    LoginAttempt,
    PasswordResetToken,
)
from apps.accounts.repositories.base import LegacyAuthRepository


class AdminUserRepository(LegacyAuthRepository):
    """Read legacy admin users without exposing password hashes by default."""

    model = AdminUser

    def list_users(self):
        """Return admin users while deferring password hashes."""
        return self.queryset().defer("password_hash").all()

    def get_user(self, admin_id):
        """Return one admin user while deferring password hash."""
        return self.queryset().defer("password_hash").get(id=admin_id)

    def get_user_for_credential_check(self, email):
        """Return credential fields for internal compatibility analysis only."""
        return self.queryset().get(email=email)


class AdminSessionRepository(LegacyAuthRepository):
    """Read legacy admin sessions."""

    model = AdminSession

    def list_sessions(self):
        """Return all admin sessions with admin relationship loaded."""
        return self.queryset().select_related("admin").all()

    def list_sessions_for_admin(self, admin_id):
        """Return sessions for one admin."""
        return self.list_sessions().filter(admin_id=admin_id)


class LoginAttemptRepository(LegacyAuthRepository):
    """Read login attempt audit records."""

    model = LoginAttempt

    def list_attempts(self):
        """Return login attempts."""
        return self.queryset().all()


class PasswordResetTokenRepository(LegacyAuthRepository):
    """Read password reset token metadata for internal validation only."""

    model = PasswordResetToken

    def list_tokens(self):
        """Return reset tokens with admin relationship loaded."""
        return self.queryset().select_related("admin").all()


class TwoFactorChallengeRepository(LegacyAuthRepository):
    """Read 2FA challenge metadata for internal validation only."""

    model = AdminTwoFactorChallenge

    def list_challenges(self):
        """Return 2FA challenges with admin relationship loaded."""
        return self.queryset().select_related("admin").all()


class AdminActivityLogRepository(LegacyAuthRepository):
    """Read admin activity logs."""

    model = AdminActivityLog

    def list_activity_logs(self):
        """Return activity logs with optional admin relationship loaded."""
        return self.queryset().select_related("admin").all()
