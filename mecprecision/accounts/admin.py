"""Cấu hình Django Admin cho Accounts."""

from django.contrib import admin

from .models import AdminActivityLog, AdminSession, AdminTwoFactorChallenge, AdminUser, AuthEmailOutbox, LoginAttempt, PasswordResetToken


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    """Màn hình quản trị tài khoản admin."""

    list_display = ("id", "full_name", "email", "role", "is_active", "two_factor_enabled", "created_at")
    search_fields = ("full_name", "email", "role")
    list_filter = ("role", "is_active", "two_factor_enabled")


@admin.register(AdminSession)
class AdminSessionAdmin(admin.ModelAdmin):
    """Màn hình xem session admin."""

    list_display = ("session_id", "admin", "email", "role", "expires_at", "last_seen_at")
    search_fields = ("session_id", "email", "remote_addr", "user_agent")


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """Màn hình xem lịch sử thử đăng nhập."""

    list_display = ("id", "email", "remote_addr", "success", "created_at")
    search_fields = ("email", "remote_addr")
    list_filter = ("success",)


admin.site.register(PasswordResetToken)
admin.site.register(AdminTwoFactorChallenge)
admin.site.register(AuthEmailOutbox)
admin.site.register(AdminActivityLog)
