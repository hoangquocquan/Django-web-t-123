"""Cấu hình Django Admin cho module AI."""

from django.contrib import admin

from .models import AIConversation, AITranslationCache, SystemSetting


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    """Màn hình xem lịch sử hỏi đáp AI."""

    list_display = ("id", "channel", "model", "provider", "status", "created_at")
    search_fields = ("channel", "user_message", "assistant_message", "error")
    list_filter = ("channel", "provider", "status")
    readonly_fields = ("created_at",)


@admin.register(AITranslationCache)
class AITranslationCacheAdmin(admin.ModelAdmin):
    """Màn hình xem cache bản dịch AI."""

    list_display = ("id", "target_language", "model", "status", "updated_at")
    search_fields = ("source_text", "translated_text", "target_language")
    list_filter = ("target_language", "status", "provider")


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    """Màn hình quản lý key/value cài đặt hệ thống."""

    list_display = ("setting_key", "setting_value")
    search_fields = ("setting_key", "setting_value")
