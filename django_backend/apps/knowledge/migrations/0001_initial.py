from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="KnowledgeDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=240)),
                ("source_type", models.CharField(default="text", max_length=32)),
                ("source_path", models.TextField(blank=True)),
                ("content", models.TextField()),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "knowledge_documents",
                "ordering": ["-id"],
            },
        ),
        migrations.CreateModel(
            name="KnowledgeChunk",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField()),
                ("chunk_index", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chunks",
                        to="knowledge.knowledgedocument",
                    ),
                ),
            ],
            options={
                "db_table": "knowledge_chunks",
                "ordering": ["document_id", "chunk_index"],
                "unique_together": {("document", "chunk_index")},
            },
        ),
        migrations.CreateModel(
            name="KnowledgeEmbedding",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("vector", models.JSONField(default=list)),
                ("model_name", models.CharField(default="local-hash-embedding", max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "chunk",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="embedding",
                        to="knowledge.knowledgechunk",
                    ),
                ),
            ],
            options={
                "db_table": "knowledge_embeddings",
            },
        ),
        migrations.AddIndex(
            model_name="knowledgedocument",
            index=models.Index(fields=["source_type"], name="knowledge_source_type_idx"),
        ),
        migrations.AddIndex(
            model_name="knowledgeembedding",
            index=models.Index(fields=["model_name"], name="knowledge_embedding_model_idx"),
        ),
    ]

