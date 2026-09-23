"""Add explicit pilot approvals and content-free evaluation records."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("knowledge", "0005_department_scope"),
        ("foundation", "0012_phase6a_capability_permissions"),
    ]

    operations = [
        migrations.AddField(
            model_name="knowledgedocument", name="owner_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="knowledgedocument", name="effective_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="knowledgedocument", name="pilot_corpus_approved",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="knowledgedocument", name="pilot_approved_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="knowledgedocument", name="pilot_approved_by_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="knowledgeuserscope", name="approval_status",
            field=models.CharField(default="PENDING", max_length=16, choices=[
                ("PENDING", "Pending"), ("APPROVED", "Approved"),
                ("REVOKED", "Revoked"),
            ]),
        ),
        migrations.AddField(
            model_name="knowledgeuserscope", name="approved_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="knowledgeuserscope", name="expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="knowledgeuserscope", name="approved_by",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="approved_knowledge_scopes", to="foundation.foundationuser",
            ),
        ),
        migrations.CreateModel(
            name="KnowledgeAssistantFeedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("category", models.CharField(max_length=24, choices=[
                    ("HELPFUL", "Helpful"), ("INCORRECT", "Incorrect"),
                    ("MISSING_SOURCE", "Missing source"), ("NEED_DOCUMENT", "Need document"),
                ])),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("interaction", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="feedback", to="knowledge.knowledgeassistantlog")),
                ("submitted_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="knowledge_feedback", to="foundation.foundationuser")),
            ],
            options={"db_table": "knowledge_assistant_feedback"},
        ),
        migrations.AddConstraint(
            model_name="knowledgeassistantfeedback",
            constraint=models.UniqueConstraint(fields=("interaction", "submitted_by"), name="knowledge_feedback_once_per_user"),
        ),
        migrations.CreateModel(
            name="KnowledgeHumanEvaluation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rating", models.CharField(max_length=24, choices=[
                    ("CORRECT", "Correct"), ("PARTIALLY_CORRECT", "Partially correct"),
                    ("INCORRECT", "Incorrect"),
                ])),
                ("citation_valid", models.BooleanField(default=False)),
                ("missing_information", models.BooleanField(default=False)),
                ("hallucination", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("interaction", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="human_evaluation", to="knowledge.knowledgeassistantlog")),
                ("reviewer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="knowledge_human_evaluations", to="foundation.foundationuser")),
            ],
            options={"db_table": "knowledge_human_evaluations"},
        ),
    ]


