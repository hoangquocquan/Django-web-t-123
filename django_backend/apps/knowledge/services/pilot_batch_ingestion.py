"""Explicit, bounded batch loading for approved pilot documents."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError

from apps.foundation.services import FoundationPermissionService
from apps.knowledge.models import KnowledgeAuditEvent, KnowledgeDocument
from apps.knowledge.services.knowledge_indexer import KnowledgeIndexer


class PilotBatchIngestionService:
    """Preflight an explicit batch before indexing any selected document."""

    MAX_BATCH_SIZE = 25

    def __init__(self, indexer=None):
        self.indexer = indexer or KnowledgeIndexer()

    def _require_admin_writer(self, actor):
        FoundationPermissionService().require_permission(actor, "knowledge", "write")
        if getattr(getattr(actor, "role", None), "name", "").lower() != "admin":
            raise PermissionDenied("Pilot batch ingestion requires an admin operator.")

    def load(self, document_ids, *, actor):
        """Index only an explicit, small, fully approved set of document IDs."""
        self._require_admin_writer(actor)
        ids = list(document_ids or [])
        if not ids or len(ids) > self.MAX_BATCH_SIZE:
            raise ValidationError(
                f"Pilot batch must contain between 1 and {self.MAX_BATCH_SIZE} documents."
            )
        if any(type(document_id) is not int or document_id <= 0 for document_id in ids):
            raise ValidationError("Pilot batch document IDs must be positive integers.")
        if len(set(ids)) != len(ids):
            raise ValidationError("Pilot batch contains duplicate document IDs.")
        documents = list(KnowledgeDocument.objects.filter(pk__in=ids))
        if len(documents) != len(ids):
            raise ValidationError("Pilot batch contains an unknown document ID.")
        by_id = {document.id: document for document in documents}
        ordered = [by_id[document_id] for document_id in ids]
        for document in ordered:
            if (
                document.status not in {"APPROVED", "INDEXED"}
                or not document.active_version
                or not document.pilot_corpus_approved
                or document.quality_review_status != "APPROVED"
                or not document.confidentiality_checked_at
            ):
                raise ValidationError(
                    f"Document {document.id} is not eligible for pilot ingestion."
                )

        loaded = []
        for document in ordered:
            indexed = self.indexer.reindex(document)
            if indexed.status != "INDEXED" or not indexed.chunks.exists():
                raise ValidationError(f"Document {indexed.id} failed post-index validation.")
            loaded.append({
                "document_id": indexed.id,
                "version": indexed.version,
                "chunk_count": indexed.chunks.count(),
            })
        KnowledgeAuditEvent.objects.create(
            event="pilot_batch_loaded", actor_id=actor.id,
            decision="allowed", source_ids=ids,
        )
        return {"loaded_count": len(loaded), "documents": loaded}


