"""Models for AI knowledge documents, permissions, and local vector search."""

from django.db import models


class DocumentCategory(models.Model):
    """Business category used to organize internal knowledge documents."""

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_document_categories"
        ordering = ["name"]

    def __str__(self):
        """Return the category name."""
        return self.name


class KnowledgeDocument(models.Model):
    """A source document that can be searched by the AI platform."""

    title = models.CharField(max_length=240)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="knowledge/documents/", blank=True)
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        related_name="documents",
        blank=True,
        null=True,
    )
    source_type = models.CharField(max_length=32, default="text")
    source_path = models.TextField(blank=True)
    content = models.TextField()
    version = models.PositiveIntegerField(default=1)
    created_by_email = models.EmailField(blank=True)
    permission_level = models.CharField(max_length=32, default="internal")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "knowledge_documents"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["source_type"], name="knowledge_source_type_idx"),
            models.Index(fields=["permission_level"], name="knowledge_permission_idx"),
        ]

    def __str__(self):
        """Return the document title."""
        return self.title


class DocumentPermission(models.Model):
    """Optional document-level access control rule."""

    document = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE, related_name="permissions")
    role_name = models.CharField(max_length=80, blank=True)
    user_email = models.EmailField(blank=True)
    can_read = models.BooleanField(default=True)
    can_write = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_document_permissions"
        indexes = [
            models.Index(fields=["role_name"], name="knowledge_perm_role_idx"),
            models.Index(fields=["user_email"], name="knowledge_perm_user_idx"),
        ]

    def __str__(self):
        """Return a short permission label."""
        return self.role_name or self.user_email or f"document-{self.document_id}"


class DocumentVersion(models.Model):
    """Immutable snapshot of document content at one version."""

    document = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE, related_name="versions")
    version = models.PositiveIntegerField()
    content = models.TextField()
    change_note = models.TextField(blank=True)
    created_by_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_document_versions"
        ordering = ["document_id", "-version"]
        unique_together = [("document", "version")]

    def __str__(self):
        """Return a document version label."""
        return f"{self.document_id}:v{self.version}"


class KnowledgeChunk(models.Model):
    """Searchable text chunk derived from a knowledge document."""

    document = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE, related_name="chunks")
    content = models.TextField()
    chunk_index = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_chunks"
        ordering = ["document_id", "chunk_index"]
        unique_together = [("document", "chunk_index")]

    def __str__(self):
        """Return a short chunk label."""
        return f"{self.document_id}:{self.chunk_index}"


class KnowledgeEmbedding(models.Model):
    """Local embedding vector for one knowledge chunk."""

    chunk = models.OneToOneField(KnowledgeChunk, on_delete=models.CASCADE, related_name="embedding")
    vector = models.JSONField(default=list)
    model_name = models.CharField(max_length=120, default="local-hash-embedding")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_embeddings"
        indexes = [
            models.Index(fields=["model_name"], name="knowledge_embedding_model_idx"),
        ]

    def __str__(self):
        """Return the related chunk label."""
        return str(self.chunk)


class KnowledgeAssistantLog(models.Model):
    """Audit log for internal AI knowledge assistant responses."""

    question = models.TextField()
    answer = models.TextField(blank=True)
    sources = models.JSONField(default=list)
    confidence = models.FloatField(default=0)
    warning = models.TextField(blank=True)
    user_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_assistant_logs"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["created_at"], name="knowledge_log_created_idx"),
            models.Index(fields=["user_email"], name="knowledge_log_user_idx"),
        ]

    def __str__(self):
        """Return a safe log label without exposing the full question."""
        return f"knowledge-assistant-log-{self.id or 'new'}"
