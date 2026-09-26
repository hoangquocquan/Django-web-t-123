"""Models for audited AI agent executions and UAT outbound approvals."""

# ruff: noqa: RUF012 - Django Meta attributes are declarative ORM configuration.

import uuid

from django.db import models
from django.db.models import Q


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


class OutboundMessageApproval(models.Model):
    """Human approval and delivery audit for one synthetic UAT LINE message."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        SENT = "SENT", "Sent"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    environment = models.CharField(max_length=16, default="uat")
    synthetic = models.BooleanField(default=True)
    rfq_id = models.CharField(max_length=80, db_index=True)
    channel = models.CharField(max_length=16, default="line")
    recipient_ref = models.CharField(max_length=255)
    proposed_message = models.TextField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    ai_payload = models.JSONField(default=dict)
    approved_by = models.ForeignKey(
        "foundation.FoundationUser",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="approved_uat_line_messages",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        "foundation.FoundationUser",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="rejected_uat_line_messages",
    )
    rejected_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    provider_message_id = models.CharField(max_length=160, null=True, blank=True)
    provider_response = models.JSONField(default=dict, blank=True)
    send_attempted = models.BooleanField(default=False)
    line_result_status = models.CharField(max_length=40, blank=True)
    audit_log = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_agent_outbound_message_approvals"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(environment="uat"),
                name="line_uat_environment_only",
            ),
            models.CheckConstraint(
                condition=Q(synthetic=True),
                name="line_uat_synthetic_only",
            ),
            models.CheckConstraint(
                condition=Q(channel="line"),
                name="line_uat_channel_only",
            ),
        ]

    def __str__(self):
        """Return the business-safe approval identifier."""
        return f"line-uat-{self.id}"
