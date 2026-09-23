"""Explicit review, approval and revocation transitions for knowledge revisions."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.foundation.services import FoundationPermissionService
from apps.knowledge.models import DocumentVersion, KnowledgeAuditEvent, KnowledgeDocument
from apps.knowledge.services.access_policy import content_hash


class KnowledgeGovernanceService:
    def _require_writer(self, actor):
        FoundationPermissionService().require_permission(actor, "knowledge", "write")

    @transaction.atomic
    def submit_review(self, document_id, *, actor):
        self._require_writer(actor)
        document = KnowledgeDocument.objects.select_for_update().get(pk=document_id)
        if document.status != "DRAFT":
            raise ValidationError("Only a draft can be submitted for review.")
        document.status = "REVIEW"
        document.save(update_fields=["status", "updated_at"])
        return document

    @transaction.atomic
    def approve(self, document_id, *, actor, release_public=False):
        self._require_writer(actor)
        if getattr(getattr(actor, "role", None), "name", "").lower() != "admin":
            raise PermissionDenied("Knowledge approval requires an admin approver.")
        document = KnowledgeDocument.objects.select_for_update().get(pk=document_id)
        if document.status != "REVIEW" or not document.active_version:
            raise ValidationError("Only a current reviewed document may be approved.")
        if document.created_by_email and document.created_by_email.lower() == actor.email.lower():
            raise PermissionDenied("The author cannot approve their own document.")
        if document.permission_level == "public" and not release_public:
            raise ValidationError("Public AI release requires an explicit approval decision.")
        if document.permission_level not in {"public", "internal", "restricted"}:
            raise ValidationError("Unknown knowledge classification.")
        if document.permission_level in {"internal", "restricted"} and document.department not in {
            "SALES", "ENGINEERING", "QC", "MANAGEMENT",
        }:
            raise ValidationError("Internal and restricted knowledge requires a department scope.")
        digest = content_hash(document.content)
        if (
            not document.owner_email
            or not document.effective_date
            or not document.owner_reviewed_at
            or document.owner_reviewed_by_email.casefold() != document.owner_email.casefold()
            or document.owner_review_hash != digest
        ):
            raise ValidationError("The named owner must review the exact effective document revision.")
        revision = DocumentVersion.objects.filter(document=document, version=document.version).first()
        if not revision or revision.content != document.content or revision.content_hash != digest:
            raise ValidationError("The current revision does not match its immutable snapshot.")
        document.status = "APPROVED"
        document.approved_version = document.version
        document.approved_at = timezone.now()
        document.approved_by_email = actor.email
        document.approval_hash = digest
        document.ai_public_approved = document.permission_level == "public" and release_public
        document.save(update_fields=["status", "approved_version", "approved_at", "approved_by_email", "approval_hash", "ai_public_approved", "updated_at"])
        KnowledgeAuditEvent.objects.create(event="approved", document=document, document_id_snapshot=document.id, version=document.version, actor_id=actor.id)
        return document

    @transaction.atomic
    def archive(self, document_id, *, actor):
        self._require_writer(actor)
        if getattr(getattr(actor, "role", None), "name", "").lower() != "admin":
            raise PermissionDenied("Knowledge archive requires an admin approver.")
        document = KnowledgeDocument.objects.select_for_update().get(pk=document_id)
        if document.status == "ARCHIVED":
            return document
        document.status = "ARCHIVED"
        document.active_version = False
        document.ai_public_approved = False
        document.pilot_corpus_approved = False
        document.save(update_fields=["status", "active_version", "ai_public_approved", "pilot_corpus_approved", "updated_at"])
        KnowledgeAuditEvent.objects.create(event="archived", document=document, document_id_snapshot=document.id, version=document.version, actor_id=actor.id)
        return document


