"""Knowledge search with source references and confidence scoring."""

from __future__ import annotations

import re
import unicodedata
import hashlib

from django.db.models import F

from apps.knowledge.services.access_policy import KnowledgeAccessPolicy
from apps.knowledge.models import KnowledgeAuditEvent
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
        policy = KnowledgeAccessPolicy()
        eligible = policy.eligible_documents(user)
        queryset = KnowledgeChunk.objects.select_related("document", "revision", "embedding", "document__category").filter(
            document__in=eligible, revision__version=F("document__version"),
            revision__content_hash=F("document__approval_hash"),
        )
        readable = [chunk for chunk in queryset if policy.can_read_chunk(chunk, user)]
        query_vector = self.embedding_service.embed(query)
        results = self.vector_store.search(
            query_vector=query_vector,
            queryset=readable,
            limit=max(limit, 100),
            provider=self.embedding_service,
        )
        results = self._rerank_with_lexical_overlap(query, readable, results, limit)
        # Approval can be revoked while embedding/scoring is in progress.
        results = [result for result in results if policy.can_read_chunk(result["chunk"], user)]
        sources = self.sources_from_results(results)
        KnowledgeAuditEvent.objects.create(
            event="query", actor_id=getattr(user, "id", None),
            decision="allowed" if sources else "denied",
            query_hash=hashlib.sha256(str(query).encode("utf-8")).hexdigest(),
            source_ids=[source["id"] for source in sources],
        )
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
            source["revision_id"] = result["chunk"].revision_id
            source["section"] = result["chunk"].section or None
            source["page"] = result["chunk"].page
            sources.append(source)
        return sources

    def confidence(self, results):
        """Return a compact confidence score based on top hit similarity."""
        if not results:
            return 0
        top_score = max(result["score"] for result in results)
        return round(min(1.0, max(0.0, top_score)), 4)

    def _rerank_with_lexical_overlap(self, query, readable, vector_results, limit):
        """Lift exact local-demo term matches above deterministic hash collisions."""
        tokens = self._tokens(query)
        by_chunk_id = {result["chunk"].id: dict(result) for result in vector_results}
        if tokens:
            minimum_score = 0.34
            for chunk in readable:
                haystack = f"{chunk.document.title} {chunk.content}"
                overlap = tokens.intersection(self._tokens(haystack))
                if not overlap:
                    continue
                lexical_score = min(0.95, minimum_score + (0.11 * len(overlap)))
                current = by_chunk_id.get(chunk.id)
                if current is None or lexical_score > current["score"]:
                    by_chunk_id[chunk.id] = {"chunk": chunk, "score": lexical_score}
        return sorted(
            by_chunk_id.values(),
            key=lambda item: (item["score"], item["chunk"].document_id * -1, item["chunk"].chunk_index * -1),
            reverse=True,
        )[:limit]

    def _tokens(self, text):
        stop_words = {"the", "and", "for", "with", "from", "this", "that"}
        normalized = unicodedata.normalize("NFKD", str(text or "").casefold())
        normalized = "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        ).replace("đ", "d")
        return {
            token
            for token in re.findall(r"[a-z0-9]+", normalized)
            if len(token) >= 3 and token not in stop_words
        }

    def _can_read(self, document, user):
        """Compatibility shim for callers; uses the same policy as list/download."""
        return KnowledgeAccessPolicy().can_read(document, user)
