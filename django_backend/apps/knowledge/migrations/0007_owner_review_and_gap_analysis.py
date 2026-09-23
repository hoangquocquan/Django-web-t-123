"""Add owner evidence and structured real-pilot evaluation dimensions."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("knowledge", "0006_controlled_pilot_evaluation"),
        ("foundation", "0010_phase4c_role_activity_and_quotation_archive"),
    ]

    operations = [
        migrations.AddField(
            model_name="knowledgedocument", name="owner_reviewed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="knowledgedocument", name="owner_reviewed_by_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="knowledgedocument", name="owner_review_hash",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="knowledgehumanevaluation", name="question_category",
            field=models.CharField(default="PRODUCT", max_length=16, choices=[
                ("PRODUCT", "Product"), ("CAPABILITY", "Capability"),
                ("RFQ", "RFQ"), ("TECHNICAL", "Technical"),
                ("QUALITY", "Quality"),
            ]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="knowledgehumanevaluation", name="permission_correct",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="KnowledgeGapReview",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("category", models.CharField(max_length=32, choices=[
                    ("MISSING_DOCUMENT", "Missing document"),
                    ("POOR_DOCUMENT_QUALITY", "Poor document quality"),
                    ("RETRIEVAL_ISSUE", "Retrieval issue"),
                    ("PERMISSION_ISSUE", "Permission issue"),
                ])),
                ("resolved", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("interaction", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="gap_review", to="knowledge.knowledgeassistantlog")),
                ("reviewer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="knowledge_gap_reviews", to="foundation.foundationuser")),
            ],
            options={"db_table": "knowledge_gap_reviews"},
        ),
    ]

