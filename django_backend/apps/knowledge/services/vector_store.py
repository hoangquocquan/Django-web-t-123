"""Vector-store contract với fallback Django JSON rõ ràng cho môi trường local."""

from __future__ import annotations

from abc import ABC, abstractmethod

from django.conf import settings

from apps.knowledge.models import KnowledgeEmbedding
from apps.knowledge.services.embedding_service import EmbeddingProvider


class VectorStore(ABC):
    """Hợp đồng lưu/tìm vector để có thể thay bằng pgvector sau này."""

    @abstractmethod
    def upsert(self, *, chunk, vector, metadata):
        """Tạo hoặc cập nhật vector của một chunk."""

    @abstractmethod
    def search(self, *, query_vector, queryset, limit, provider):
        """Tìm các chunk gần nhất."""

    @abstractmethod
    def delete(self, *, chunk_ids):
        """Xóa vector theo chunk ID."""

    @abstractmethod
    def health_check(self):
        """Mô tả trạng thái backend vector."""


class DjangoJSONVectorStore(VectorStore):
    """Fallback local dùng JSONField; không được xem là production vector engine."""

    backend_name = "django-json-development-fallback"

    def upsert(self, *, chunk, vector, metadata):
        embedding, _created = KnowledgeEmbedding.objects.update_or_create(
            chunk=chunk,
            defaults={
                "vector": vector,
                "provider": metadata["provider"],
                "model_name": metadata["model_name"],
                "dimension": metadata["dimension"],
                "embedding_version": metadata["embedding_version"],
                "content_hash": metadata["content_hash"],
            },
        )
        return embedding

    def search(self, *, query_vector, queryset, limit, provider):
        hits = []
        expected_dimension = len(query_vector)
        minimum_score = float(getattr(settings, "KNOWLEDGE_MIN_RELEVANCE_SCORE", 0.5))
        for chunk in queryset:
            try:
                embedding = chunk.embedding
            except KnowledgeEmbedding.DoesNotExist:
                continue
            if embedding.dimension and embedding.dimension != expected_dimension:
                continue
            if embedding.provider != provider.provider_name:
                continue
            score = EmbeddingProvider.similarity(query_vector, embedding.vector)
            if score >= minimum_score:
                hits.append({"chunk": chunk, "score": score})
        return sorted(hits, key=lambda item: item["score"], reverse=True)[:limit]

    def delete(self, *, chunk_ids):
        return KnowledgeEmbedding.objects.filter(chunk_id__in=list(chunk_ids)).delete()[0]

    def health_check(self):
        return {
            "available": True,
            "backend": self.backend_name,
            "production_ready": False,
            "warning": "Use PostgreSQL with pgvector before high-scale production deployment.",
        }
