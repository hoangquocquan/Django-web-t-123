from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("slug", models.SlugField(max_length=140, unique=True)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "knowledge_document_categories",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="knowledgedocument",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="knowledgedocument",
            name="file",
            field=models.FileField(blank=True, upload_to="knowledge/documents/"),
        ),
        migrations.AddField(
            model_name="knowledgedocument",
            name="version",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="knowledgedocument",
            name="created_by_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="knowledgedocument",
            name="permission_level",
            field=models.CharField(default="internal", max_length=32),
        ),
        migrations.AddField(
            model_name="knowledgedocument",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="knowledgedocument",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="documents",
                to="knowledge.documentcategory",
            ),
        ),
        migrations.CreateModel(
            name="DocumentPermission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role_name", models.CharField(blank=True, max_length=80)),
                ("user_email", models.EmailField(blank=True, max_length=254)),
                ("can_read", models.BooleanField(default=True)),
                ("can_write", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="permissions",
                        to="knowledge.knowledgedocument",
                    ),
                ),
            ],
            options={
                "db_table": "knowledge_document_permissions",
            },
        ),
        migrations.CreateModel(
            name="DocumentVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.PositiveIntegerField()),
                ("content", models.TextField()),
                ("change_note", models.TextField(blank=True)),
                ("created_by_email", models.EmailField(blank=True, max_length=254)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="versions",
                        to="knowledge.knowledgedocument",
                    ),
                ),
            ],
            options={
                "db_table": "knowledge_document_versions",
                "ordering": ["document_id", "-version"],
                "unique_together": {("document", "version")},
            },
        ),
        migrations.CreateModel(
            name="KnowledgeAssistantLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question", models.TextField()),
                ("answer", models.TextField(blank=True)),
                ("sources", models.JSONField(default=list)),
                ("confidence", models.FloatField(default=0)),
                ("warning", models.TextField(blank=True)),
                ("user_email", models.EmailField(blank=True, max_length=254)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "knowledge_assistant_logs",
                "ordering": ["-id"],
            },
        ),
        migrations.AddIndex(
            model_name="knowledgedocument",
            index=models.Index(fields=["permission_level"], name="knowledge_permission_idx"),
        ),
        migrations.AddIndex(
            model_name="documentpermission",
            index=models.Index(fields=["role_name"], name="knowledge_perm_role_idx"),
        ),
        migrations.AddIndex(
            model_name="documentpermission",
            index=models.Index(fields=["user_email"], name="knowledge_perm_user_idx"),
        ),
        migrations.AddIndex(
            model_name="knowledgeassistantlog",
            index=models.Index(fields=["created_at"], name="knowledge_log_created_idx"),
        ),
        migrations.AddIndex(
            model_name="knowledgeassistantlog",
            index=models.Index(fields=["user_email"], name="knowledge_log_user_idx"),
        ),
    ]
