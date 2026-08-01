"""Models for audited AI agent executions."""

from django.db import models


class AgentRun(models.Model):
    """One local AI agent execution record."""

    request_text = models.TextField()
    request_hash = models.CharField(max_length=64, blank=True, db_index=True)
    correlation_id = models.CharField(max_length=64, blank=True, db_index=True)
    status = models.CharField(max_length=32, default="completed")
    state_history = models.JSONField(default=list, blank=True)
    selected_tools = models.JSONField(default=list)
    result = models.JSONField(default=dict)
    created_by_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_agent_runs"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["status"], name="ai_agent_status_idx"),
        ]

    def __str__(self):
        """Return a short label without exposing full request text."""
        return f"agent-run-{self.id or 'new'}"


class AgentToolAudit(models.Model):
    """Security audit for one allow-listed, read-only agent tool call."""

    run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name="tool_audits")
    correlation_id = models.CharField(max_length=64, db_index=True)
    user_email = models.EmailField(blank=True)
    tool_name = models.CharField(max_length=120)
    required_permission = models.CharField(max_length=120)
    input_hash = models.CharField(max_length=64)
    output_summary = models.JSONField(default=dict, blank=True)
    latency_ms = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=32)
    error = models.CharField(max_length=500, blank=True)
    policy_decision = models.CharField(max_length=80, default="ALLOW_READ_ONLY")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_agent_tool_audits"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["tool_name", "status"], name="ai_tool_name_status_idx"),
        ]
