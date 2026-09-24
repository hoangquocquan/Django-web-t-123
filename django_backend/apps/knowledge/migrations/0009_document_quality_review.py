"""Add an explicit structured quality decision before pilot admission."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("knowledge", "0008_pilot_program_launch_gate")]

    operations = [
        migrations.AddField(
            model_name="knowledgedocument", name="quality_review_status",
            field=models.CharField(default="PENDING", max_length=16, choices=[
                ("PENDING", "Pending"), ("APPROVED", "Approved"),
                ("REJECTED", "Rejected"),
            ]),
        ),
        migrations.AddField(
            model_name="knowledgedocument", name="quality_review_reason",
            field=models.CharField(blank=True, max_length=32, choices=[
                ("INCOMPLETE", "Incomplete"), ("OUTDATED", "Outdated"),
                ("CONFIDENTIAL", "Confidential"),
                ("INVALID_METADATA", "Invalid metadata"),
            ]),
        ),
        migrations.AddField(
            model_name="knowledgedocument", name="quality_reviewed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="knowledgedocument", name="quality_reviewed_by_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
    ]
