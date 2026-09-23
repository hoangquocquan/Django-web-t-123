"""Add default-deny department scope without activating existing users/documents."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("knowledge", "0004_governance_access"),
        ("foundation", "0010_phase4c_role_activity_and_quotation_archive"),
    ]

    operations = [
        migrations.AddField(
            model_name="knowledgedocument", name="department",
            field=models.CharField(blank=True, default="", max_length=16, choices=[
                ("", "Unassigned"), ("SALES", "Sales"),
                ("ENGINEERING", "Engineering"), ("QC", "QC"),
                ("MANAGEMENT", "Management"),
            ]),
        ),
        migrations.CreateModel(
            name="KnowledgeUserScope",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("department", models.CharField(max_length=16, choices=[
                    ("SALES", "Sales"), ("ENGINEERING", "Engineering"),
                    ("QC", "QC"), ("MANAGEMENT", "Management"),
                ])),
                ("pilot_enabled", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(to="foundation.foundationuser", related_name="knowledge_scope", on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={"db_table": "knowledge_user_scopes"},
        ),
    ]

