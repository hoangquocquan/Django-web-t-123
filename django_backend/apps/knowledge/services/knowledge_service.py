"""Application services for ingestion and semantic search."""

from __future__ import annotations

from django.db import transaction

from apps.knowledge.models import KnowledgeChunk, KnowledgeDocument, KnowledgeEmbedding
from apps.knowledge.services.embedding_service import LocalEmbeddingService
from apps.knowledge.services.text_processing import TextProcessor


def document_to_dict(document):
    """Convert a knowledge document into API JSON."""
    return {
        "id": document.id,
        "title": document.title,
        "source_type": document.source_type,
        "source_path": document.source_path,
        "metadata": document.metadata,
        "created_at": document.created_at.isoformat() if document.created_at else None,
    }


def search_result_to_dict(result):
    """Convert one search hit into API JSON."""
    chunk = result["chunk"]
    return {
        "score": round(result["score"], 4),
        "chunk": {
            "id": chunk.id,
            "content": chunk.content,
            "chunk_index": chunk.chunk_index,
        },
        "document": document_to_dict(chunk.document),
    }


class KnowledgeService:
    """Own document ingestion and local RAG search."""

    def __init__(self, text_processor=None, embedding_service=None):
        """Allow tests to inject deterministic doubles if needed."""
        self.text_processor = text_processor or TextProcessor()
        self.embedding_service = embedding_service or LocalEmbeddingService()

    @transaction.atomic
    def ingest_text(self, title, content, source_type="text", source_path="", metadata=None):
        """Create a document, chunks, and local embeddings."""
        document = KnowledgeDocument.objects.create(
            title=str(title or "").strip() or "Untitled document",
            content=content,
            source_type=source_type,
            source_path=source_path,
            metadata=metadata or {},
        )
        chunks = self.text_processor.chunk_text(content)
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

    def ingest_file(self, file_path, title=None, metadata=None):
        """Ingest a local document path into the knowledge database."""
        content = self.text_processor.extract_text(file_path)
        suffix = str(file_path).rsplit(".", 1)[-1].lower() if "." in str(file_path) else "text"
        return self.ingest_text(
            title=title or str(file_path),
            content=content,
            source_type=suffix,
            source_path=str(file_path),
            metadata=metadata or {},
        )

    def search(self, query, limit=5):
        """Search knowledge chunks by local vector similarity."""
        query_vector = self.embedding_service.embed(query)
        hits = []
        queryset = KnowledgeChunk.objects.select_related("document", "embedding").all()
        for chunk in queryset:
            score = self.embedding_service.similarity(query_vector, chunk.embedding.vector)
            if score > 0:
                hits.append({"chunk": chunk, "score": score})
        return sorted(hits, key=lambda item: item["score"], reverse=True)[:limit]

