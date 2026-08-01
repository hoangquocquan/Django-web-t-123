"""Lập chỉ mục tài liệu bằng embedding thật và thay thế dữ liệu theo giao dịch an toàn."""

from __future__ import annotations

import hashlib

from django.db import transaction

from apps.knowledge.models import DocumentVersion, KnowledgeChunk, KnowledgeEmbedding
from apps.knowledge.services.embedding_service import get_embedding_provider
from apps.knowledge.services.text_processing import TextProcessor
from apps.knowledge.services.vector_store import DjangoJSONVectorStore


class KnowledgeIndexer:
    """Chuẩn bị toàn bộ vector trước, sau đó mới thay index cũ trong một transaction."""

    def __init__(self, text_processor=None, embedding_service=None, vector_store=None):
        self.text_processor = text_processor or TextProcessor()
        self.embedding_service = embedding_service or get_embedding_provider()
        self.vector_store = vector_store or DjangoJSONVectorStore()

    def reindex(self, document, created_by_email="", change_note=""):
        """Không xóa index cũ nếu Ollama hoặc batch embedding thất bại."""
        clean_content = self.text_processor.clean_text(document.content)
        chunks = self.text_processor.chunk_text(clean_content)
        vectors = self.embedding_service.embed_batch(chunks) if chunks else []
        prepared = list(zip(chunks, vectors))

        with transaction.atomic():
            document.chunks.all().delete()
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
            for index, (chunk_text, vector) in enumerate(prepared):
                chunk = KnowledgeChunk.objects.create(document=document, content=chunk_text, chunk_index=index)
                self.vector_store.upsert(
                    chunk=chunk,
                    vector=vector,
                    metadata={
                        "provider": self.embedding_service.provider_name,
                        "model_name": self.embedding_service.model_name,
                        "dimension": len(vector),
                        "embedding_version": self.embedding_service.embedding_version,
                        "content_hash": self.content_hash(chunk_text),
                    },
                )
        return document

    def needs_reindex(self, document):
        """Phát hiện thiếu index, đổi model/provider hoặc nội dung đã thay đổi."""
        chunks = list(document.chunks.select_related("embedding").all())
        expected_chunks = self.text_processor.chunk_text(self.text_processor.clean_text(document.content))
        if len(chunks) != len(expected_chunks):
            return True
        for chunk, expected_content in zip(chunks, expected_chunks):
            try:
                embedding = chunk.embedding
            except KnowledgeEmbedding.DoesNotExist:
                return True
            if (
                embedding.provider != self.embedding_service.provider_name
                or embedding.model_name != self.embedding_service.model_name
                or embedding.embedding_version != self.embedding_service.embedding_version
                or embedding.content_hash != self.content_hash(expected_content)
            ):
                return True
        return False

    @staticmethod
    def content_hash(content):
        return hashlib.sha256(str(content).encode("utf-8")).hexdigest()
