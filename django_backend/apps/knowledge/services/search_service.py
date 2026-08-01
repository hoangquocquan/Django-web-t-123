"""Knowledge search with source references and confidence scoring."""

from __future__ import annotations

from apps.knowledge.models import KnowledgeChunk
from apps.knowledge.services.embedding_service import get_embedding_provider
from apps.knowledge.services.knowledge_service import document_to_dict, search_result_to_dict
from apps.knowledge.services.vector_store import DjangoJSONVectorStore


class KnowledgeSearchService:
    """Search local knowledge vectors and format RAG evidence."""

    def __init__(self, embedding_service=None, vector_store=None):
        """Allow tests to inject a deterministic embedding service."""
        self.embedding_service = embedding_service or get_embedding_provider()
        self.vector_store = vector_store or DjangoJSONVectorStore()

    def search(self, query, limit=5, user=None):
        """Return ranked chunks, source documents, and confidence."""
        query_vector = self.embedding_service.embed(query)
        queryset = KnowledgeChunk.objects.select_related("document", "embedding", "document__category").all()
        readable = [chunk for chunk in queryset if self._can_read(chunk.document, user)]
        results = self.vector_store.search(
            query_vector=query_vector,
            queryset=readable,
            limit=limit,
            provider=self.embedding_service,
        )
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
            source = document_to_dict(document)
            source["relevance_score"] = round(result.get("score", 0), 4)
            sources.append(source)
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
