"""Models for AI knowledge documents and local vector search."""

from django.db import models


class KnowledgeDocument(models.Model):
    """A source document that can be searched by the AI platform."""

    title = models.CharField(max_length=240)
    source_type = models.CharField(max_length=32, default="text")
    source_path = models.TextField(blank=True)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_documents"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["source_type"], name="knowledge_source_type_idx"),
        ]

    def __str__(self):
        """Return the document title."""
        return self.title


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

