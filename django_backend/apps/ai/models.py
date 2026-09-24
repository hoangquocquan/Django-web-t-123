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


class AIGovernanceEvent(models.Model):
    """Audit AI policy decisions such as allow, block, or rate-limit."""

    DECISION_ALLOWED = "allowed"
    DECISION_BLOCKED = "blocked"
    DECISION_RATE_LIMITED = "rate_limited"

    user_email = models.EmailField(blank=True)
    role_name = models.CharField(max_length=80, blank=True)
    organization_id = models.CharField(max_length=120, blank=True)
    module = models.CharField(max_length=80, blank=True)
    endpoint = models.CharField(max_length=160)
    action = models.CharField(max_length=80, default="unknown")
    tool_name = models.CharField(max_length=120, blank=True)
    request_source = models.CharField(max_length=80, default="api")
    decision = models.CharField(max_length=40)
    reason = models.CharField(max_length=240, blank=True)
    request_hash = models.CharField(max_length=64, blank=True)
    policy_version = models.CharField(max_length=80, default="ai-policy-v2.0")
    matched_rule_ids = models.JSONField(default=list, blank=True)
    redaction_summary = models.JSONField(default=dict, blank=True)
    correlation_id = models.CharField(max_length=64, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_governance_events"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["decision"], name="ai_gov_decision_idx"),
            models.Index(fields=["endpoint"], name="ai_gov_endpoint_idx"),
            models.Index(fields=["created_at"], name="ai_gov_created_idx"),
        ]

    def __str__(self):
        """Return a compact governance audit label."""
        return f"{self.endpoint}:{self.decision}:{self.id or 'new'}"
