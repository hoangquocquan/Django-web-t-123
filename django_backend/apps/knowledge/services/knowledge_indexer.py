"""Lập chỉ mục tài liệu bằng embedding thật và thay thế dữ liệu theo giao dịch an toàn."""

from __future__ import annotations

import hashlib

from django.core.exceptions import PermissionDenied
from django.db import transaction

from apps.knowledge.models import KnowledgeAuditEvent, KnowledgeChunk, KnowledgeDocument, KnowledgeEmbedding
from apps.knowledge.services.access_policy import KnowledgeAccessPolicy
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
        """Never embed a draft or publish a revoked/changed revision."""
        policy = KnowledgeAccessPolicy()
        document.refresh_from_db()
        if not policy.can_index(document):
            raise PermissionDenied("Only an approved current revision may be indexed.")
        approved_hash = document.approval_hash
        approved_version = document.version
        clean_content = self.text_processor.clean_text(document.content)
        if self.content_hash(clean_content) != approved_hash:
            raise PermissionDenied("Approved content changed before embedding.")
        chunks = self.text_processor.chunk_text(clean_content)
        vectors = self.embedding_service.embed_batch(chunks) if chunks else []
        prepared = list(zip(chunks, vectors))

        with transaction.atomic():
            current = KnowledgeDocument.objects.select_for_update().get(pk=document.pk)
            if (not policy.can_index(current) or current.approval_hash != approved_hash
                    or current.version != approved_version):
                raise PermissionDenied("Approval changed during indexing.")
            revision = current.versions.get(version=approved_version, content_hash=approved_hash)
            current.chunks.all().delete()
            for index, (chunk_text, vector) in enumerate(prepared):
                chunk = KnowledgeChunk.objects.create(
                    document=current, revision=revision, content=chunk_text,
                    chunk_index=index, section=f"Chunk {index + 1}",
                )
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
            current.status = "INDEXED"
            current.save(update_fields=["status", "updated_at"])
            KnowledgeAuditEvent.objects.create(event="indexed", document=current, document_id_snapshot=current.id, version=current.version)
        document.refresh_from_db()
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


