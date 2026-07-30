"""Index knowledge documents into chunks and local vector embeddings."""

from __future__ import annotations

from django.db import transaction

from apps.knowledge.models import DocumentVersion, KnowledgeChunk, KnowledgeEmbedding
from apps.knowledge.services.embedding_service import LocalEmbeddingService
from apps.knowledge.services.text_processing import TextProcessor


class KnowledgeIndexer:
    """Create searchable chunks and embeddings for one document."""

    def __init__(self, text_processor=None, embedding_service=None):
        """Allow tests to inject deterministic collaborators."""
        self.text_processor = text_processor or TextProcessor()
        self.embedding_service = embedding_service or LocalEmbeddingService()

    @transaction.atomic
    def reindex(self, document, created_by_email="", change_note=""):
        """Replace old chunks and embeddings with a fresh index."""
        document.chunks.all().delete()
        clean_content = self.text_processor.clean_text(document.content)
        document.content = clean_content
        document.save(update_fields=["content", "updated_at"])
        DocumentVersion.objects.get_or_create(
            document=document,
            version=document.version,
            defaults={
                "content": clean_content,
                "change_note": change_note,
                "created_by_email": created_by_email,
            },
        )
        chunks = self.text_processor.chunk_text(clean_content)
        for index, chunk_text in enumerate(chunks):
            chunk = KnowledgeChunk.objects.create(
                document=document,
                content=chunk_text,
                chunk_index=index,
            )
            KnowledgeEmbedding.objects.create(
                chunk=chunk,
                vector=self.embedding_service.embed(chunk_text),
                model_name=self.embedding_service.model_name,
            )
        return document

