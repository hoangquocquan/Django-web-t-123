"""Operational health and quality checks for the local RAG runtime."""

from __future__ import annotations

from apps.ai.services.health_service import OllamaHealthService
from apps.knowledge.models import KnowledgeChunk, KnowledgeDocument, KnowledgeEmbedding
from apps.knowledge.services.embedding_service import get_embedding_provider
from apps.knowledge.services.knowledge_indexer import KnowledgeIndexer
from apps.knowledge.services.vector_store import DjangoJSONVectorStore


class KnowledgeRuntimeHealthService:
    """Report model, vector coverage, and reindex readiness without reading document text."""

    def __init__(
        self,
        ollama_health=None,
        embedding_provider=None,
        vector_store=None,
        indexer=None,
    ):
        self.ollama_health = ollama_health or OllamaHealthService()
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.vector_store = vector_store or DjangoJSONVectorStore()
        self.indexer = indexer or KnowledgeIndexer(
            embedding_service=self.embedding_provider,
            vector_store=self.vector_store,
        )

    def check(self):
        documents = KnowledgeDocument.objects.prefetch_related(
            "chunks__embedding"
        ).all()
        document_count = documents.count()
        chunk_count = KnowledgeChunk.objects.count()
        embedding_count = KnowledgeEmbedding.objects.count()
        stale_document_ids = [
            document.id
            for document in documents
            if self.indexer.needs_reindex(document)
        ]
        embedding_health = self.embedding_provider.health_check()
        vector_health = self.vector_store.health_check()
        generation_health = self.ollama_health.check()
        ready = bool(
            generation_health.get("model_available")
            and embedding_health.get("model_available")
            and document_count > 0
            and chunk_count > 0
            and not stale_document_ids
            and chunk_count == embedding_count
        )
        return {
            "status": "ready" if ready else "degraded",
            "generation": generation_health,
            "embedding": embedding_health,
            "vector_store": vector_health,
            "index": {
                "documents": document_count,
                "chunks": chunk_count,
                "embeddings": embedding_count,
                "coverage": round(embedding_count / chunk_count, 4)
                if chunk_count
                else 1.0,
                "stale_document_ids": stale_document_ids,
                "reindex_command": "python manage.py reindex_knowledge_embeddings",
            },
        }
