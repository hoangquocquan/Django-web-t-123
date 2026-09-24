"""Application services for ingestion and semantic search."""

from __future__ import annotations

from django.db import transaction
from django.db.models import F

from apps.knowledge.models import DocumentCategory, DocumentVersion, KnowledgeChunk, KnowledgeDocument
from apps.knowledge.services.access_policy import KnowledgeAccessPolicy, content_hash
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
        "version": document.version,
        "active_version": document.active_version,
        "approved_version": document.approved_version,
        "ai_public_approved": document.ai_public_approved,
        "revision_date": (document.versions.filter(version=document.version).values_list("created_at", flat=True).first() or document.created_at).isoformat(),
        "status": document.status,
        "created_by_email": document.created_by_email,
        "permission_level": document.permission_level,
        "department": document.department,
        "owner_email": document.owner_email,
        "effective_date": document.effective_date.isoformat() if document.effective_date else None,
        "owner_reviewed_at": document.owner_reviewed_at.isoformat() if document.owner_reviewed_at else None,
        "owner_reviewed_by_email": document.owner_reviewed_by_email,
        "quality_review_status": document.quality_review_status,
        "quality_review_reason": document.quality_review_reason or None,
        "quality_reviewed_at": document.quality_reviewed_at.isoformat() if document.quality_reviewed_at else None,
        "confidentiality_checked_at": document.confidentiality_checked_at.isoformat() if document.confidentiality_checked_at else None,
        "pilot_corpus_approved": document.pilot_corpus_approved,
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
            "section": chunk.section or None,
            "page": chunk.page,
            "revision_id": chunk.revision_id,
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
        department="",
        owner_email="",
        effective_date=None,
        created_by_email="",
        metadata=None,
    ):
        """Create an unindexed draft and immutable initial revision."""
        category = self._category_from_name(category_name)
        cleaned = self.text_processor.clean_text(content)
        document = KnowledgeDocument.objects.create(
            title=str(title or "").strip() or "Untitled document",
            description=description or "",
            category=category,
            content=cleaned,
            source_type=source_type,
            source_path=source_path,
            permission_level=permission_level or "internal",
            department=department or "",
            owner_email=owner_email or "",
            effective_date=effective_date,
            created_by_email=created_by_email or "",
            metadata=metadata or {},
        )
        DocumentVersion.objects.create(
            document=document, version=document.version, content=cleaned,
            content_hash=content_hash(cleaned), change_note="Initial draft",
            created_by_email=created_by_email,
        )
        return document

    def list_documents(self, user=None):
        """Return documents visible to the current user."""
        return KnowledgeAccessPolicy().eligible_documents(user).select_related("category")

    @transaction.atomic
    def ingest_text(self, title, content, source_type="text", source_path="", metadata=None):
        """Create a draft; explicit review and approval precede indexing."""
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

    def search(self, query, limit=5, user=None):
        """Retain raw-hit contract but enforce the shared policy before scoring."""
        policy = KnowledgeAccessPolicy()
        eligible = policy.eligible_documents(user)
        queryset = KnowledgeChunk.objects.select_related("document", "revision", "embedding").filter(
            document__in=eligible, revision__version=F("document__version"),
        )
        readable = [chunk for chunk in queryset if policy.can_read_chunk(chunk, user)]
        query_vector = self.embedding_service.embed(query)
        hits = self.vector_store.search(
            query_vector=query_vector,
            queryset=readable,
            limit=limit,
            provider=self.embedding_service,
        )
        return [hit for hit in hits if policy.can_read_chunk(hit["chunk"], user)]

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
