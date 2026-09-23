"""Add the global default-deny pilot launch state."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("knowledge", "0007_owner_review_and_gap_analysis"),
        ("foundation", "0010_phase4c_role_activity_and_quotation_archive"),
    ]

    operations = [
        migrations.CreateModel(
            name="KnowledgePilotProgram",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("status", models.CharField(default="DRAFT", max_length=16, choices=[
                    ("DRAFT", "Draft"), ("RUNNING", "Running"),
                    ("SUSPENDED", "Suspended"), ("COMPLETED", "Completed"),
                ])),
                ("planned_start", models.DateField(blank=True, null=True)),
                ("planned_end", models.DateField(blank=True, null=True)),
                ("launched_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="approved_knowledge_pilot_programs", to="foundation.foundationuser")),
            ],
            options={"db_table": "knowledge_pilot_programs"},
        ),
    ]

