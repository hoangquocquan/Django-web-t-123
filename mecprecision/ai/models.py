"""Django models cho module AI.

Module AI hiện map vào bảng cũ để lưu lịch sử hỏi đáp và cache bản dịch.
Nhờ lưu database, admin có thể xem lại AI đã trả lời gì, dùng model nào,
trạng thái thật hay fallback demo.
"""

from django.db import models
from django.utils import timezone


class AIConversation(models.Model):
    """Một lượt hỏi đáp AI, dùng chung cho chatbot public và AI trong Admin."""

    channel = models.CharField(max_length=80, default="public")
    user_message = models.TextField()
    assistant_message = models.TextField(blank=True, null=True)
    model = models.CharField(max_length=120, blank=True, null=True)
    provider = models.CharField(max_length=80, default="ollama")
    status = models.CharField(max_length=40, default="ok")
    error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "ai_conversations"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.channel} - {self.user_message[:60]}"


class AITranslationCache(models.Model):
    """Cache bản dịch để lần sau không cần gọi AI lại với cùng nội dung."""

    source_hash = models.CharField(max_length=128)
    source_text = models.TextField()
    target_language = models.CharField(max_length=80)
    translated_text = models.TextField()
    provider = models.CharField(max_length=80, default="ollama")
    model = models.CharField(max_length=120, blank=True, null=True)
    status = models.CharField(max_length=40, default="ok")
    error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "ai_translation_cache"
        unique_together = ("source_hash", "target_language", "model")
        ordering = ["-id"]

    def __str__(self):
        return f"{self.target_language} - {self.source_hash}"


class SystemSetting(models.Model):
    """Cài đặt hệ thống dạng key/value, ví dụ model Ollama mặc định."""

    setting_key = models.CharField(max_length=255, primary_key=True)
    setting_value = models.TextField()

    class Meta:
        managed = False
        db_table = "system_settings"

    def __str__(self):
        return self.setting_key
