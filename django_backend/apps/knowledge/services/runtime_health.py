"""Operational health and quality checks for the local RAG runtime."""

from __future__ import annotations

from django.db.models import Count

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
        active_signature = {
            "provider": self.embedding_provider.provider_name,
            "model_name": self.embedding_provider.model_name,
            "dimension": self.embedding_provider.dimensions,
        }
        stored_signatures = list(
            KnowledgeEmbedding.objects.values("provider", "model_name", "dimension")
            .annotate(count=Count("id"))
            .order_by("provider", "model_name", "dimension")
        )
        incompatible_signatures = [
            signature
            for signature in stored_signatures
            if signature["provider"] != active_signature["provider"]
            or signature["model_name"] != active_signature["model_name"]
            or signature["dimension"] != active_signature["dimension"]
        ]
        ready = bool(
            generation_health.get("model_available")
            and embedding_health.get("available", embedding_health.get("model_available"))
            and document_count > 0
            and chunk_count > 0
            and not stale_document_ids
            and chunk_count == embedding_count
            and not incompatible_signatures
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
                "active_embedding_signature": active_signature,
                "stored_embedding_signatures": stored_signatures,
                "incompatible_embedding_signatures": incompatible_signatures,
                "stale_document_ids": stale_document_ids,
                "reindex_command": "python manage.py reindex_knowledge_embeddings",
            },
        }
