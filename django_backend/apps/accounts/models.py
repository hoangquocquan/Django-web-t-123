"""Read-only unmanaged ORM models for legacy authentication tables."""

from django.db import models

from apps.common.models import LegacyReadOnlyModel


class AdminUser(LegacyReadOnlyModel):
    """Legacy CMS admin user."""

    id = models.IntegerField(primary_key=True)
    full_name = models.TextField()
    email = models.TextField(unique=True)
    password_hash = models.TextField()
    role = models.TextField(default="editor")
    is_active = models.BooleanField(default=True)
    avatar_url = models.TextField(blank=True, null=True)
    two_factor_enabled = models.BooleanField(default=False)
    created_at = models.TextField()

    class Meta:
        managed = False
        db_table = "admin_users"
        ordering = ["id"]

    def __str__(self):
        return self.email


class AdminSession(LegacyReadOnlyModel):
    """Legacy admin session stored in SQLite."""

    session_id = models.TextField(primary_key=True)
    admin = models.ForeignKey(
        AdminUser,
        db_column="admin_id",
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    full_name = models.TextField()
    email = models.TextField()
    role = models.TextField()
    expires_at = models.IntegerField()
    remote_addr = models.TextField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    last_seen_at = models.IntegerField(blank=True, null=True)
    created_at = models.TextField()

    class Meta:
        managed = False
        db_table = "admin_sessions"
        ordering = ["-last_seen_at", "-created_at"]

    def __str__(self):
        return self.email


class LoginAttempt(LegacyReadOnlyModel):
    """Legacy login attempt audit row."""

    id = models.IntegerField(primary_key=True)
    email = models.TextField()
    remote_addr = models.TextField(blank=True, null=True)
    success = models.BooleanField(default=False)
    created_at = models.IntegerField()

    class Meta:
        managed = False
        db_table = "login_attempts"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.email


class PasswordResetToken(LegacyReadOnlyModel):
    """Legacy password reset token metadata."""

    token = models.TextField(primary_key=True)
    admin = models.ForeignKey(
        AdminUser,
        db_column="admin_id",
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    email = models.TextField()
    expires_at = models.IntegerField()
    used_at = models.IntegerField(blank=True, null=True)
    created_at = models.TextField()

    class Meta:
        managed = False
        db_table = "password_reset_tokens"
        ordering = ["-created_at"]

    def __str__(self):
        return self.email


class AdminTwoFactorChallenge(LegacyReadOnlyModel):
    """Legacy one-time 2FA challenge metadata."""

    challenge_id = models.TextField(primary_key=True)
    admin = models.ForeignKey(
        AdminUser,
        db_column="admin_id",
        on_delete=models.CASCADE,
        related_name="two_factor_challenges",
    )
    code = models.TextField()
    used_at = models.TextField(blank=True, null=True)
    created_at = models.TextField()

    class Meta:
        managed = False
        db_table = "admin_2fa_challenges"
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.admin_id)


class AdminActivityLog(LegacyReadOnlyModel):
    """Legacy CMS admin activity log."""

    id = models.IntegerField(primary_key=True)
    admin = models.ForeignKey(
        AdminUser,
        db_column="admin_id",
        on_delete=models.SET_NULL,
        related_name="activity_logs",
        blank=True,
        null=True,
    )
    actor_name = models.TextField(blank=True, null=True)
    action = models.TextField()
    target_type = models.TextField(blank=True, null=True)
    target_id = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    remote_addr = models.TextField(blank=True, null=True)
    created_at = models.TextField()

    class Meta:
        managed = False
        db_table = "admin_activity_logs"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.action
