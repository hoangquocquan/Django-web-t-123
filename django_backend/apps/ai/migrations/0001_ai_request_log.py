"""Create lightweight AI request monitoring table."""

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AIRequestLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("request_type", models.CharField(default="knowledge_rag", max_length=80)),
                ("user_email", models.EmailField(blank=True, max_length=254)),
                ("question_hash", models.CharField(blank=True, max_length=64)),
                ("question_preview", models.CharField(blank=True, max_length=240)),
                ("retrieved_documents", models.JSONField(blank=True, default=list)),
                ("model_name", models.CharField(blank=True, max_length=120)),
                ("provider", models.CharField(default="ollama-local", max_length=80)),
                ("response_time_ms", models.PositiveIntegerField(default=0)),
                ("confidence", models.FloatField(default=0)),
                ("status", models.CharField(default="success", max_length=40)),
                ("warning", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "ai_request_logs",
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="airequestlog",
            index=models.Index(fields=["request_type"], name="ai_request_type_idx"),
        ),
        migrations.AddIndex(
            model_name="airequestlog",
            index=models.Index(fields=["created_at"], name="ai_request_created_idx"),
        ),
        migrations.AddIndex(
            model_name="airequestlog",
            index=models.Index(fields=["model_name"], name="ai_request_model_idx"),
        ),
    ]

