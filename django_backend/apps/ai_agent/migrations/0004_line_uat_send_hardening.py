"""Bind approval content and persist an at-most-once send claim."""

# ruff: noqa: RUF012 - Django migration class attributes are declarative.

import hashlib
import json

from django.db import migrations, models


def backfill_approved_content_hashes(apps, schema_editor):
    """Bind any pre-existing approved or terminal UAT rows before constraints."""
    approval_model = apps.get_model("ai_agent", "OutboundMessageApproval")
    db_alias = schema_editor.connection.alias
    rows = approval_model.objects.using(db_alias).filter(
        status__in=["APPROVED", "SENT", "FAILED"], approved_content_hash=""
    )
    for approval in rows.iterator():
        canonical = json.dumps(
            {
                "channel": approval.channel,
                "environment": approval.environment,
                "message": approval.proposed_message,
                "recipient_ref": approval.recipient_ref,
                "rfq_id": approval.rfq_id,
                "synthetic": approval.synthetic,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        approval.approved_content_hash = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()
        approval.save(update_fields=["approved_content_hash"])


def no_reverse(apps, schema_editor):
    """Retain harmless hashes when reversing only the constraints."""


class Migration(migrations.Migration):
    dependencies = [("ai_agent", "0003_outboundmessageapproval")]

    operations = [
        migrations.AddField(
            model_name="outboundmessageapproval",
            name="approved_content_hash",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="outboundmessageapproval",
            name="send_claimed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_approved_content_hashes, no_reverse),
        migrations.AddConstraint(
            model_name="outboundmessageapproval",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("status__in", ["PENDING", "APPROVED", "REJECTED", "SENT", "FAILED"])
                ),
                name="line_uat_known_status_only",
            ),
        ),
        migrations.AddConstraint(
            model_name="outboundmessageapproval",
            constraint=models.CheckConstraint(
                condition=(
                    ~models.Q(("status__in", ["APPROVED", "SENT", "FAILED"]))
                    | ~models.Q(("approved_content_hash", ""))
                ),
                name="line_uat_approved_content_bound",
            ),
        ),
    ]
