"""Single fail-closed eligibility and document authorization policy."""

from __future__ import annotations

import hashlib

from django.db.models import Exists, F, OuterRef, Q
from django.utils import timezone

from apps.foundation.services import FoundationPermissionService
from apps.knowledge.models import (
    DocumentPermission, DocumentVersion, KnowledgeDocument, KnowledgeUserScope,
)


def content_hash(content):
    return hashlib.sha256(str(content).encode("utf-8")).hexdigest()


class KnowledgeAccessPolicy:
    """Apply approval and principal grants before search ranking or disclosure."""

    def eligible_documents(self, user=None):
        revisions = DocumentVersion.objects.filter(
            document_id=OuterRef("pk"),
            version=OuterRef("version"),
            content_hash=OuterRef("approval_hash"),
            content=OuterRef("content"),
        )
        base = KnowledgeDocument.objects.filter(
            status__in=["APPROVED", "INDEXED"],
            active_version=True,
            approved_version=F("version"),
            approved_at__isnull=False,
        ).exclude(approval_hash="").exclude(approved_by_email="").annotate(_has_revision=Exists(revisions)).filter(_has_revision=True)

        public = Q(permission_level="public", ai_public_approved=True)
        if user is None:
            return base.filter(public)
        if not FoundationPermissionService().has_permission(user, "knowledge", "read"):
            return base.none()
        from apps.knowledge.services.pilot_program import PilotProgramService
        if not PilotProgramService().is_running():
            return base.none()

        scope = KnowledgeUserScope.objects.filter(
            user=user, pilot_enabled=True, approval_status="APPROVED",
            approved_at__isnull=False, training_acknowledged_at__isnull=False,
        ).filter(Q(expires_at__isnull=True) | Q(expires_at__gte=timezone.now())).first()
        if scope is None:
            return base.none()

        base = base.filter(pilot_corpus_approved=True)

        role_name = getattr(getattr(user, "role", None), "name", "")
        email = getattr(user, "email", "")
        matches = Q()
        if role_name:
            matches |= Q(role_name=role_name)
        if email:
            matches |= Q(user_email=email)
        if not matches:
            return base.filter(public)
        grants = DocumentPermission.objects.filter(document_id=OuterRef("pk")).filter(matches)
        internal_scope = Q(permission_level="internal", department=scope.department)
        return base.annotate(
            _grant=Exists(grants.filter(can_read=True)),
            _deny=Exists(grants.filter(can_read=False)),
        ).filter(
            public | internal_scope | Q(permission_level__in=["internal", "restricted"], _grant=True),
            _deny=False,
        )

    def can_read(self, document, user=None):
        if document.pk is None or content_hash(document.content) != document.approval_hash:
            return False
        return self.eligible_documents(user).filter(pk=document.pk).exists()

    def can_read_chunk(self, chunk, user=None):
        document = chunk.document
        return (
            chunk.revision_id is not None
            and chunk.revision.document_id == document.id
            and chunk.revision.version == document.version
            and chunk.revision.content_hash == document.approval_hash
            and self.can_read(document, user)
        )

    def can_index(self, document):
        """Approval gate independent of audience; public needs separate release approval."""
        if document.status not in {"APPROVED", "INDEXED"} or not document.active_version:
            return False
        if document.approved_version != document.version or not document.approved_at:
            return False
        if document.permission_level not in {"public", "internal", "restricted"}:
            return False
        if (
            not document.owner_email
            or not document.effective_date
            or not document.owner_reviewed_at
            or document.owner_reviewed_by_email.casefold() != document.owner_email.casefold()
            or document.owner_review_hash != content_hash(document.content)
        ):
            return False
        if document.permission_level in {"internal", "restricted"} and document.department not in {
            "SALES", "ENGINEERING", "QC", "MANAGEMENT",
        }:
            return False
        if document.permission_level == "public" and not document.ai_public_approved:
            return False
        if not document.approval_hash or content_hash(document.content) != document.approval_hash:
            return False
        return DocumentVersion.objects.filter(
            document=document, version=document.version,
            content_hash=document.approval_hash, content=document.content,
        ).exists()

    def sources_still_readable(self, sources, user=None):
        """Reauthorize immutable citations after model generation/revocation races."""
        for source in sources:
            if any(type(source.get(key)) is not int for key in ("id", "revision_id", "version")):
                return False
            document = KnowledgeDocument.objects.filter(pk=source.get("id")).first()
            if (document is None or not self.can_read(document, user)
                    or source.get("version") != document.version
                    or not DocumentVersion.objects.filter(
                        pk=source.get("revision_id"), document=document,
                        version=document.version, content_hash=document.approval_hash,
                    ).exists()):
                return False
        return True
