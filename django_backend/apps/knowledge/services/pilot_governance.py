"""Approval gates for the small, controlled internal AI pilot."""

from __future__ import annotations

import re

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.foundation.services import FoundationPermissionService
from apps.knowledge.models import KnowledgeAuditEvent, KnowledgeDocument, KnowledgeUserScope
from apps.knowledge.services.access_policy import content_hash


PROHIBITED_PILOT_PATTERNS = {
    "quotation": r"\b(quotation|quote price|báo giá)\b",
    "cost": r"\b(cost|giá vốn)\b",
    "margin": r"\b(margin|biên lợi nhuận)\b",
    "customer_confidential": r"\b(customer confidential|khách hàng bảo mật)\b",
    "supplier_confidential": r"\b(supplier confidential|nhà cung cấp bảo mật)\b",
}


class PilotGovernanceService:
    """Require explicit admin approval for each pilot user and corpus item."""

    def _require_admin_writer(self, actor):
        FoundationPermissionService().require_permission(actor, "knowledge", "write")
        if getattr(getattr(actor, "role", None), "name", "").lower() != "admin":
            raise PermissionDenied("Pilot approval requires an admin approver.")

    @transaction.atomic
    def record_owner_review(self, document_id, *, actor):
        """Bind the named owner's confirmation to the exact reviewed content."""
        FoundationPermissionService().require_permission(actor, "knowledge", "write")
        document = KnowledgeDocument.objects.select_for_update().get(pk=document_id)
        if document.status != "REVIEW":
            raise ValidationError("Owner review requires a document in REVIEW status.")
        if not document.owner_email:
            raise ValidationError("A document owner is required before owner review.")
        if actor.email.casefold() != document.owner_email.casefold():
            raise PermissionDenied("Only the named document owner may confirm owner review.")
        document.owner_reviewed_at = timezone.now()
        document.owner_reviewed_by_email = actor.email
        document.owner_review_hash = content_hash(document.content)
        document.save(update_fields=[
            "owner_reviewed_at", "owner_reviewed_by_email", "owner_review_hash",
            "updated_at",
        ])
        KnowledgeAuditEvent.objects.create(
            event="owner_reviewed", document=document,
            document_id_snapshot=document.id, version=document.version,
            actor_id=actor.id, decision="allowed",
        )
        return document

    @transaction.atomic
    def record_quality_review(self, document_id, *, actor, decision, rejection_reason=""):
        """Record an independent structured document-quality decision."""
        self._require_admin_writer(actor)
        document = KnowledgeDocument.objects.select_for_update().get(pk=document_id)
        if document.status not in {"APPROVED", "INDEXED"}:
            raise ValidationError("Quality review requires an approved document.")
        if decision not in {"APPROVED", "REJECTED"}:
            raise ValidationError("Unknown quality-review decision.")
        allowed_reasons = {"INCOMPLETE", "OUTDATED", "CONFIDENTIAL", "INVALID_METADATA"}
        if decision == "REJECTED":
            if rejection_reason not in allowed_reasons:
                raise ValidationError("A structured rejection reason is required.")
            document.quality_review_reason = rejection_reason
            document.pilot_corpus_approved = False
        else:
            if not document.owner_email or not document.effective_date or not document.department and document.permission_level != "public":
                raise ValidationError("Document quality metadata is incomplete.")
            if document.effective_date > timezone.localdate():
                raise ValidationError("A future document is not current for pilot use.")
            if len(str(document.content or "").strip()) < 20:
                raise ValidationError("Document content is incomplete.")
            matches = [
                label for label, pattern in PROHIBITED_PILOT_PATTERNS.items()
                if re.search(pattern, document.content, flags=re.IGNORECASE)
            ]
            if matches:
                raise ValidationError(
                    "Document contains prohibited information classes: " + ", ".join(matches)
                )
            document.quality_review_reason = ""
        document.quality_review_status = decision
        document.quality_reviewed_at = timezone.now()
        document.quality_reviewed_by_email = actor.email
        document.confidentiality_checked_at = timezone.now()
        document.confidentiality_checked_by_email = actor.email
        document.save(update_fields=[
            "quality_review_status", "quality_review_reason",
            "quality_reviewed_at", "quality_reviewed_by_email",
            "confidentiality_checked_at", "confidentiality_checked_by_email",
            "pilot_corpus_approved", "updated_at",
        ])
        KnowledgeAuditEvent.objects.create(
            event="quality_reviewed", document=document,
            document_id_snapshot=document.id, version=document.version,
            actor_id=actor.id, decision="allowed" if decision == "APPROVED" else "denied",
        )
        return document

    @transaction.atomic
    def approve_user_scope(self, scope_id, *, actor, expires_at=None):
        self._require_admin_writer(actor)
        scope = KnowledgeUserScope.objects.select_for_update().select_related("user").get(pk=scope_id)
        if scope.user_id == actor.id:
            raise PermissionDenied("A pilot user cannot approve their own access.")
        if not scope.user.is_active:
            raise ValidationError("An inactive user cannot join the pilot.")
        scope.approval_status = "APPROVED"
        scope.pilot_enabled = True
        scope.approved_by = actor
        scope.approved_at = timezone.now()
        scope.expires_at = expires_at
        scope.save(update_fields=[
            "approval_status", "pilot_enabled", "approved_by", "approved_at",
            "expires_at", "updated_at",
        ])
        KnowledgeAuditEvent.objects.create(
            event="pilot_user_approved", actor_id=actor.id,
            decision="allowed", source_ids=[],
        )
        return scope

    @transaction.atomic
    def revoke_user_scope(self, scope_id, *, actor):
        self._require_admin_writer(actor)
        scope = KnowledgeUserScope.objects.select_for_update().get(pk=scope_id)
        scope.approval_status = "REVOKED"
        scope.pilot_enabled = False
        scope.training_acknowledged_at = None
        scope.save(update_fields=[
            "approval_status", "pilot_enabled", "training_acknowledged_at", "updated_at",
        ])
        KnowledgeAuditEvent.objects.create(
            event="pilot_user_revoked", actor_id=actor.id,
            decision="allowed", source_ids=[],
        )
        return scope

    @transaction.atomic
    def acknowledge_training(self, scope_id, *, actor):
        """Record the pilot user's own acknowledgement of the usage guide."""
        scope = KnowledgeUserScope.objects.select_for_update().get(pk=scope_id)
        if scope.user_id != actor.id:
            raise PermissionDenied("A user may acknowledge training only for their own scope.")
        if scope.approval_status != "APPROVED" or not scope.pilot_enabled:
            raise PermissionDenied("Pilot access must be approved before onboarding acknowledgement.")
        scope.training_acknowledged_at = timezone.now()
        scope.save(update_fields=["training_acknowledged_at", "updated_at"])
        KnowledgeAuditEvent.objects.create(
            event="training_ack", actor_id=actor.id, decision="allowed", source_ids=[],
        )
        return scope

    @transaction.atomic
    def approve_document(self, document_id, *, actor):
        self._require_admin_writer(actor)
        document = KnowledgeDocument.objects.select_for_update().get(pk=document_id)
        if document.status not in {"APPROVED", "INDEXED"} or not document.active_version:
            raise ValidationError("Only an approved active document may enter the pilot corpus.")
        if not document.owner_email or not document.effective_date:
            raise ValidationError("Pilot documents require an owner and effective date.")
        if document.quality_review_status != "APPROVED" or not document.quality_reviewed_at:
            raise ValidationError("Pilot documents require an approved quality review.")
        if not document.confidentiality_checked_at:
            raise ValidationError("Pilot documents require confidentiality review evidence.")
        if (
            not document.owner_reviewed_at
            or document.owner_reviewed_by_email.casefold() != document.owner_email.casefold()
            or document.owner_review_hash != content_hash(document.content)
        ):
            raise ValidationError("The named owner must review the exact document revision.")
        if document.permission_level in {"internal", "restricted"} and not document.department:
            raise ValidationError("Internal pilot documents require a department.")
        matches = [
            label for label, pattern in PROHIBITED_PILOT_PATTERNS.items()
            if re.search(pattern, document.content, flags=re.IGNORECASE)
        ]
        if matches:
            raise ValidationError(
                "Pilot corpus contains prohibited information classes: " + ", ".join(matches)
            )
        corpus_limit = int(getattr(settings, "AI_PILOT_CORPUS_MAX_DOCUMENTS", 100))
        current_count = KnowledgeDocument.objects.filter(pilot_corpus_approved=True).exclude(
            pk=document.pk
        ).count()
        if current_count >= corpus_limit:
            raise ValidationError(f"Pilot corpus limit of {corpus_limit} documents reached.")
        document.pilot_corpus_approved = True
        document.pilot_approved_at = timezone.now()
        document.pilot_approved_by_email = actor.email
        document.save(update_fields=[
            "pilot_corpus_approved", "pilot_approved_at",
            "pilot_approved_by_email", "updated_at",
        ])
        KnowledgeAuditEvent.objects.create(
            event="pilot_doc_approved", document=document,
            document_id_snapshot=document.id, version=document.version,
            actor_id=actor.id, decision="allowed",
        )
        return document
