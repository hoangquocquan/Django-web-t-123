"""Add AI governance audit events."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0001_ai_request_log"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIGovernanceEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_email", models.EmailField(blank=True, max_length=254)),
                ("endpoint", models.CharField(max_length=160)),
                ("action", models.CharField(default="unknown", max_length=80)),
                ("decision", models.CharField(max_length=40)),
                ("reason", models.CharField(blank=True, max_length=240)),
                ("request_hash", models.CharField(blank=True, max_length=64)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "ai_governance_events",
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="aigovernanceevent",
            index=models.Index(fields=["decision"], name="ai_gov_decision_idx"),
        ),
        migrations.AddIndex(
            model_name="aigovernanceevent",
            index=models.Index(fields=["endpoint"], name="ai_gov_endpoint_idx"),
        ),
        migrations.AddIndex(
            model_name="aigovernanceevent",
            index=models.Index(fields=["created_at"], name="ai_gov_created_idx"),
        ),
    ]

