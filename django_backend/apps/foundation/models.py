"""Managed Django models for foundation ownership."""

# ruff: noqa: RUF012 - Django Meta attributes are declarative ORM configuration.

from django.db import models


class FoundationPermission(models.Model):
    """Django-owned permission action for one module."""

    code = models.CharField(max_length=120, unique=True)
    module = models.CharField(max_length=80)
    action = models.CharField(max_length=40)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "foundation_permissions"
        ordering = ["module", "action"]
        unique_together = [("module", "action")]

    def __str__(self):
        """Return the permission code."""
        return self.code


class FoundationRole(models.Model):
    """Django-owned role used by foundation users."""

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        FoundationPermission,
        through="FoundationRolePermission",
        related_name="roles",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "foundation_roles"
        ordering = ["name"]

    def __str__(self):
        """Return the role name."""
        return self.name


class FoundationRolePermission(models.Model):
    """Django-owned role-to-permission relationship."""

    role = models.ForeignKey(FoundationRole, on_delete=models.CASCADE)
    permission = models.ForeignKey(FoundationPermission, on_delete=models.CASCADE)

    class Meta:
        db_table = "foundation_role_permissions"
        unique_together = [("role", "permission")]


class FoundationUser(models.Model):
    """Django-owned user account for admin/foundation access."""

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=160)
    password_hash = models.CharField(max_length=256)
    role = models.ForeignKey(
        FoundationRole, on_delete=models.PROTECT, related_name="users"
    )
    is_active = models.BooleanField(default=True)
    legacy_admin_id = models.IntegerField(blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "foundation_users"
        ordering = ["id"]

    def __str__(self):
        """Return the user email."""
        return self.email

    @property
    def is_authenticated(self):
        """Let DRF treat a valid foundation user as authenticated."""
        return True

    @property
    def is_anonymous(self):
        """Foundation users returned by token auth are never anonymous."""
        return False


class FoundationUserProfile(models.Model):
    """Django-owned profile data for a foundation user."""

    user = models.OneToOneField(
        FoundationUser, on_delete=models.CASCADE, related_name="profile"
    )
    avatar_url = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    language = models.CharField(max_length=10, default="vi")
    timezone = models.CharField(max_length=80, default="Asia/Tokyo")
    two_factor_enabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "foundation_user_profiles"

    def __str__(self):
        """Return the related user email."""
        return self.user.email


class FoundationAuthToken(models.Model):
    """Django-owned API session token metadata."""

    user = models.ForeignKey(
        FoundationUser, on_delete=models.CASCADE, related_name="tokens"
    )
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(blank=True, null=True)
    remote_addr = models.CharField(max_length=80, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = "foundation_auth_tokens"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["token_hash"], name="foundation_token_hash_idx"),
            models.Index(fields=["expires_at"], name="foundation_token_exp_idx"),
        ]

    def __str__(self):
        """Return token owner email without exposing the token."""
        return self.user.email


class FoundationLoginAttempt(models.Model):
    """Security audit event for successful and failed login attempts."""

    email_hash = models.CharField(max_length=64, db_index=True)
    remote_addr_hash = models.CharField(max_length=64, blank=True, db_index=True)
    success = models.BooleanField(default=False)
    reason = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "foundation_login_attempts"
        ordering = ["-created_at", "-id"]


class FoundationTwoFactorChallenge(models.Model):
    """Short-lived one-time challenge used by a future 2FA delivery adapter."""

    user = models.ForeignKey(
        FoundationUser,
        on_delete=models.CASCADE,
        related_name="two_factor_challenges",
    )
    challenge_id = models.CharField(max_length=64, unique=True)
    code_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(blank=True, null=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "foundation_two_factor_challenges"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["challenge_id", "expires_at"], name="foundation_2fa_lookup_idx"
            ),
        ]
