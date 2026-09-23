"""Fail-closed governance metadata; legacy documents remain DRAFT/unbound."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("knowledge", "0003_knowledgeembedding_content_hash_and_more")]

    operations = [
        migrations.AddField(model_name="knowledgedocument", name="status", field=models.CharField(max_length=16, default="DRAFT", choices=[("DRAFT", "Draft"), ("REVIEW", "Review"), ("APPROVED", "Approved"), ("INDEXED", "Indexed"), ("ARCHIVED", "Archived")])),
        migrations.AddField(model_name="knowledgedocument", name="active_version", field=models.BooleanField(default=True)),
        migrations.AddField(model_name="knowledgedocument", name="approved_version", field=models.PositiveIntegerField(null=True, blank=True)),
        migrations.AddField(model_name="knowledgedocument", name="approved_at", field=models.DateTimeField(null=True, blank=True)),
        migrations.AddField(model_name="knowledgedocument", name="approved_by_email", field=models.EmailField(blank=True, max_length=254)),
        migrations.AddField(model_name="knowledgedocument", name="approval_hash", field=models.CharField(max_length=64, blank=True)),
        migrations.AddField(model_name="knowledgedocument", name="ai_public_approved", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="documentversion", name="content_hash", field=models.CharField(max_length=64, blank=True)),
        migrations.AddField(model_name="knowledgechunk", name="revision", field=models.ForeignKey(to="knowledge.documentversion", on_delete=django.db.models.deletion.CASCADE, related_name="chunks", null=True, blank=True)),
        migrations.AddField(model_name="knowledgechunk", name="section", field=models.CharField(max_length=240, blank=True)),
        migrations.AddField(model_name="knowledgechunk", name="page", field=models.PositiveIntegerField(null=True, blank=True)),
        migrations.CreateModel(name="KnowledgeAuditEvent", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("event", models.CharField(max_length=32)),
            ("document_id_snapshot", models.PositiveIntegerField(null=True, blank=True)),
            ("version", models.PositiveIntegerField(null=True, blank=True)),
            ("actor_id", models.PositiveIntegerField(null=True, blank=True)),
            ("decision", models.CharField(max_length=16, default="allowed")),
            ("query_hash", models.CharField(max_length=64, blank=True)),
            ("source_ids", models.JSONField(default=list, blank=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("document", models.ForeignKey(to="knowledge.knowledgedocument", on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True)),
        ], options={"db_table": "knowledge_audit_events", "indexes": [models.Index(fields=["event", "created_at"], name="knowledge_audit_event_idx")]}),
    ]


