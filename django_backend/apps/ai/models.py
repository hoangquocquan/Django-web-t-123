"""Django-owned AI monitoring models."""

from django.db import models


class AIRequestLog(models.Model):
    """Audit lightweight AI usage without storing full sensitive prompts."""

    request_type = models.CharField(max_length=80, default="knowledge_rag")
    user_email = models.EmailField(blank=True)
    question_hash = models.CharField(max_length=64, blank=True)
    question_preview = models.CharField(max_length=240, blank=True)
    retrieved_documents = models.JSONField(default=list, blank=True)
    model_name = models.CharField(max_length=120, blank=True)
    provider = models.CharField(max_length=80, default="ollama-local")
    response_time_ms = models.PositiveIntegerField(default=0)
    confidence = models.FloatField(default=0)
    status = models.CharField(max_length=40, default="success")
    warning = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_request_logs"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["request_type"], name="ai_request_type_idx"),
            models.Index(fields=["created_at"], name="ai_request_created_idx"),
            models.Index(fields=["model_name"], name="ai_request_model_idx"),
        ]

    def __str__(self):
        """Return a safe log label."""
        return f"{self.request_type}:{self.status}:{self.id or 'new'}"

