"""Django models cho module Accounts.

Module này dùng bảng admin cũ thay vì thay bằng `django.contrib.auth.User`.
Như vậy website cũ và Django mới có thể cùng đọc một database trong giai đoạn migrate.
"""

from django.db import models
from django.utils import timezone


class AdminUser(models.Model):
    """Tài khoản quản trị CMS."""

    ROLE_ADMIN = "admin"
    ROLE_EDITOR = "editor"
    ROLE_VIEWER = "viewer"
    ROLE_CHOICES = [(ROLE_ADMIN, "Admin"), (ROLE_EDITOR, "Editor"), (ROLE_VIEWER, "Viewer")]

    full_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    password_hash = models.TextField()
    role = models.CharField(max_length=40, choices=ROLE_CHOICES, default=ROLE_EDITOR)
    is_active = models.BooleanField(default=True)
    avatar_url = models.TextField(blank=True, null=True)
    two_factor_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "admin_users"
        ordering = ["-id"]

    def __str__(self):
        return self.full_name


class AdminSession(models.Model):
    """Session đăng nhập admin lưu trong database."""

    session_id = models.CharField(max_length=255, primary_key=True)
    admin = models.ForeignKey(AdminUser, on_delete=models.CASCADE, db_column="admin_id", related_name="sessions")
    full_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    role = models.CharField(max_length=40)
    expires_at = models.IntegerField()
    remote_addr = models.CharField(max_length=120, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    last_seen_at = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "admin_sessions"
        ordering = ["-created_at"]

    def __str__(self):
        return self.session_id


class LoginAttempt(models.Model):
    """Lịch sử đăng nhập, dùng để audit và chống brute force cơ bản."""

    email = models.EmailField(max_length=255)
    remote_addr = models.CharField(max_length=120, blank=True, null=True)
    success = models.BooleanField(default=False)
    created_at = models.IntegerField()

    class Meta:
        managed = False
        db_table = "login_attempts"
        ordering = ["-id"]


class PasswordResetToken(models.Model):
    """Token reset mật khẩu, chỉ dùng một lần và có thời hạn."""

    token = models.CharField(max_length=255, primary_key=True)
    admin = models.ForeignKey(AdminUser, on_delete=models.CASCADE, db_column="admin_id")
    email = models.EmailField(max_length=255)
    expires_at = models.IntegerField()
    used_at = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "password_reset_tokens"


class AdminTwoFactorChallenge(models.Model):
    """Mã xác thực 2FA dùng một lần."""

    challenge_id = models.CharField(max_length=255, primary_key=True)
    admin = models.ForeignKey(AdminUser, on_delete=models.CASCADE, db_column="admin_id")
    code = models.CharField(max_length=20)
    used_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "admin_2fa_challenges"


class AuthEmailOutbox(models.Model):
    """Outbox email demo cho reset password local."""

    recipient = models.EmailField(max_length=255)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "auth_email_outbox"
        ordering = ["-id"]


class AdminActivityLog(models.Model):
    """Nhật ký hoạt động của admin trong CMS."""

    admin = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, blank=True, null=True, db_column="admin_id")
    actor_name = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=120)
    target_type = models.CharField(max_length=120, blank=True, null=True)
    target_id = models.CharField(max_length=120, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    remote_addr = models.CharField(max_length=120, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "admin_activity_logs"
        ordering = ["-id"]
