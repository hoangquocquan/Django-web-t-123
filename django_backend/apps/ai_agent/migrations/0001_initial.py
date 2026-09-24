from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AgentRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("request_text", models.TextField()),
                ("status", models.CharField(default="completed", max_length=32)),
                ("selected_tools", models.JSONField(default=list)),
                ("result", models.JSONField(default=dict)),
                ("created_by_email", models.EmailField(blank=True, max_length=254)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "ai_agent_runs",
                "ordering": ["-id"],
            },
        ),
        migrations.AddIndex(
            model_name="agentrun",
            index=models.Index(fields=["status"], name="ai_agent_status_idx"),
        ),
    ]

