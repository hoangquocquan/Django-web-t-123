"""Application services for ingestion and semantic search."""

from __future__ import annotations

from django.db import transaction

from apps.knowledge.models import DocumentCategory, KnowledgeChunk, KnowledgeDocument
from apps.knowledge.services.embedding_service import get_embedding_provider
from apps.knowledge.services.knowledge_indexer import KnowledgeIndexer
from apps.knowledge.services.text_processing import TextProcessor
from apps.knowledge.services.vector_store import DjangoJSONVectorStore


def document_to_dict(document):
    """Convert a knowledge document into API JSON."""
    return {
        "id": document.id,
        "title": document.title,
        "description": document.description,
        "category": document.category.name if document.category else None,
        "source_type": document.source_type,
        "source_path": document.source_path,
        "version": document.version,
        "created_by_email": document.created_by_email,
        "permission_level": document.permission_level,
        "metadata": document.metadata,
        "created_at": document.created_at.isoformat() if document.created_at else None,
        "updated_at": document.updated_at.isoformat() if document.updated_at else None,
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

    def __init__(self, text_processor=None, embedding_service=None, vector_store=None):
        """Allow tests to inject deterministic doubles if needed."""
        self.text_processor = text_processor or TextProcessor()
        self.embedding_service = embedding_service or get_embedding_provider()
        self.vector_store = vector_store or DjangoJSONVectorStore()

    @transaction.atomic
    def create_document(
        self,
        title,
        content,
        description="",
        category_name="",
        source_type="text",
        source_path="",
        permission_level="internal",
        created_by_email="",
        metadata=None,
    ):
        """Create a managed document and index it for semantic search."""
        category = self._category_from_name(category_name)
        document = KnowledgeDocument.objects.create(
            title=str(title or "").strip() or "Untitled document",
            description=description or "",
            category=category,
            content=content,
            source_type=source_type,
            source_path=source_path,
            permission_level=permission_level or "internal",
            created_by_email=created_by_email or "",
            metadata=metadata or {},
        )
        KnowledgeIndexer(
            text_processor=self.text_processor,
            embedding_service=self.embedding_service,
        ).reindex(document, created_by_email=created_by_email, change_note="Initial ingestion")
        return document

    def list_documents(self, user=None):
        """Return documents visible to the current user."""
        queryset = KnowledgeDocument.objects.select_related("category").all()
        if not user:
            return queryset.none()
        if getattr(getattr(user, "role", None), "name", "") == "admin":
            return queryset
        return queryset.filter(permission_level__in=["public", "internal"])

    @transaction.atomic
    def ingest_text(self, title, content, source_type="text", source_path="", metadata=None):
        """Create a document, chunks, and local embeddings."""
        return self.create_document(
            title=title,
            content=content,
            source_type=source_type,
            source_path=source_path,
            metadata=metadata,
        )

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
        """Search chunks for internal service callers without API permission filtering."""
        query_vector = self.embedding_service.embed(query)
        queryset = KnowledgeChunk.objects.select_related("document", "embedding").all()
        return self.vector_store.search(
            query_vector=query_vector,
            queryset=queryset,
            limit=limit,
            provider=self.embedding_service,
        )

    def _category_from_name(self, category_name):
        """Create or reuse a document category from a display name."""
        normalized = str(category_name or "").strip()
        if not normalized:
            return None
        slug = normalized.lower().replace(" ", "-")
        category, _created = DocumentCategory.objects.get_or_create(
            slug=slug,
            defaults={"name": normalized},
        )
        return category
