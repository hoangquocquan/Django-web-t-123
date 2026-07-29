"""Models for audited AI agent executions."""

from django.db import models


class AgentRun(models.Model):
    """One local AI agent execution record."""

    request_text = models.TextField()
    status = models.CharField(max_length=32, default="completed")
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

