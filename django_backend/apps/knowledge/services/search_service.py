"""Knowledge search with source references and confidence scoring."""

from __future__ import annotations

from apps.knowledge.models import KnowledgeChunk
from apps.knowledge.services.embedding_service import LocalEmbeddingService
from apps.knowledge.services.knowledge_service import document_to_dict, search_result_to_dict


class KnowledgeSearchService:
    """Search local knowledge vectors and format RAG evidence."""

    def __init__(self, embedding_service=None):
        """Allow tests to inject a deterministic embedding service."""
        self.embedding_service = embedding_service or LocalEmbeddingService()

    def search(self, query, limit=5, user=None):
        """Return ranked chunks, source documents, and confidence."""
        query_vector = self.embedding_service.embed(query)
        hits = []
        queryset = KnowledgeChunk.objects.select_related("document", "embedding", "document__category").all()
        for chunk in queryset:
            if not self._can_read(chunk.document, user):
                continue
            score = self.embedding_service.similarity(query_vector, chunk.embedding.vector)
            if score > 0:
                hits.append({"chunk": chunk, "score": score})
        results = sorted(hits, key=lambda item: item["score"], reverse=True)[:limit]
        sources = self.sources_from_results(results)
        return {
            "results": [search_result_to_dict(result) for result in results],
            "sources": sources,
            "confidence": self.confidence(results),
        }

    def sources_from_results(self, results):
        """Return unique source documents from search results."""
        seen = set()
        sources = []
        for result in results:
            document = result["chunk"].document
            if document.id in seen:
                continue
            seen.add(document.id)
            sources.append(document_to_dict(document))
        return sources

    def confidence(self, results):
        """Return a compact confidence score based on top hit similarity."""
        if not results:
            return 0
        top_score = max(result["score"] for result in results)
        return round(min(1.0, max(0.0, top_score)), 4)

    def _can_read(self, document, user):
        """Check document-level read access without bypassing Django permissions."""
        if document.permission_level == "public":
            return True
        if not user:
            return False
        role_name = getattr(getattr(user, "role", None), "name", "")
        if role_name == "admin":
            return True
        explicit = document.permissions.filter(can_read=True).filter(user_email=getattr(user, "email", "")).exists()
        role_allowed = document.permissions.filter(can_read=True, role_name=role_name).exists()
        return document.permission_level == "internal" or explicit or role_allowed

