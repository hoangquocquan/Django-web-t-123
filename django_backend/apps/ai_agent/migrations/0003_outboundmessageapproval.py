# Generated for the synthetic n8n + LINE UAT approval boundary.

# ruff: noqa: RUF012 - Django migration class attributes are declarative.

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_agent", "0002_agentrun_correlation_id_agentrun_request_hash_and_more"),
        ("foundation", "0010_phase4c_role_activity_and_quotation_archive"),
    ]

    operations = [
        migrations.CreateModel(
            name="OutboundMessageApproval",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("environment", models.CharField(default="uat", max_length=16)),
                ("synthetic", models.BooleanField(default=True)),
                ("rfq_id", models.CharField(db_index=True, max_length=80)),
                ("channel", models.CharField(default="line", max_length=16)),
                ("recipient_ref", models.CharField(max_length=255)),
                ("proposed_message", models.TextField()),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("APPROVED", "Approved"), ("REJECTED", "Rejected"), ("SENT", "Sent"), ("FAILED", "Failed")], db_index=True, default="PENDING", max_length=16)),
                ("ai_payload", models.JSONField(default=dict)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("rejected_at", models.DateTimeField(blank=True, null=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("provider_message_id", models.CharField(blank=True, max_length=160, null=True)),
                ("provider_response", models.JSONField(blank=True, default=dict)),
                ("send_attempted", models.BooleanField(default=False)),
                ("line_result_status", models.CharField(blank=True, max_length=40)),
                ("audit_log", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="approved_uat_line_messages", to="foundation.foundationuser")),
                ("rejected_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="rejected_uat_line_messages", to="foundation.foundationuser")),
            ],
            options={
                "db_table": "ai_agent_outbound_message_approvals",
                "ordering": ["-created_at"],
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("environment", "uat")), name="line_uat_environment_only"),
                    models.CheckConstraint(condition=models.Q(("synthetic", True)), name="line_uat_synthetic_only"),
                    models.CheckConstraint(condition=models.Q(("channel", "line")), name="line_uat_channel_only"),
                ],
            },
        ),
    ]
