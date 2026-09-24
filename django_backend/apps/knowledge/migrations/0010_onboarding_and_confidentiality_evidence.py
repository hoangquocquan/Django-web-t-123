"""Add user onboarding and confidentiality-review evidence."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("knowledge", "0009_document_quality_review")]

    operations = [
        migrations.AddField(
            model_name="knowledgedocument", name="confidentiality_checked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="knowledgedocument", name="confidentiality_checked_by_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="knowledgeuserscope", name="training_acknowledged_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="knowledgegapreview", name="category",
            field=models.CharField(max_length=32, choices=[
                ("MISSING_DOCUMENT", "Missing document"),
                ("WRONG_DOCUMENT", "Wrong document"),
                ("POOR_DOCUMENT_QUALITY", "Poor document quality"),
                ("RETRIEVAL_ISSUE", "Retrieval issue"),
                ("PERMISSION_ISSUE", "Permission issue"),
            ]),
        ),
    ]
