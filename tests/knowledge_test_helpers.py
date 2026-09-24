"""Reusable governed-knowledge fixtures for backend compatibility tests."""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from apps.foundation.models import (
    FoundationPermission,
    FoundationRole,
    FoundationUser,
)
from apps.knowledge.models import KnowledgePilotProgram, KnowledgeUserScope
from apps.knowledge.services.access_policy import content_hash
from apps.knowledge.services.embedding_service import DevelopmentHashEmbeddingProvider
from apps.knowledge.services.governance import KnowledgeGovernanceService
from apps.knowledge.services.knowledge_indexer import KnowledgeIndexer
from apps.knowledge.services.knowledge_service import KnowledgeService
from apps.knowledge.services.pilot_governance import PilotGovernanceService


def _permission(code: str):
    module, action = code.split(":", 1)
    permission, _created = FoundationPermission.objects.get_or_create(
        code=code,
        defaults={"module": module, "action": action},
    )
    return permission


def _fixture_user(email: str, role_name: str, permissions: tuple[str, ...]):
    role, _created = FoundationRole.objects.get_or_create(name=role_name)
    role.permissions.add(*[_permission(code) for code in permissions])
    user, _created = FoundationUser.objects.get_or_create(
        email=email,
        defaults={
            "full_name": role_name,
            "password_hash": "test-only",
            "role": role,
        },
    )
    if user.role_id != role.id:
        user.role = role
        user.save(update_fields=["role", "updated_at"])
    return user


def ensure_running_pilot():
    """Create the bounded runtime state needed by internal retrieval tests."""

    today = timezone.localdate()
    program, _created = KnowledgePilotProgram.objects.update_or_create(
        name="FIRST_INTERNAL_AI_PILOT",
        defaults={
            "status": "RUNNING",
            "planned_start": today - timedelta(days=1),
            "planned_end": today + timedelta(days=14),
        },
    )
    return program


def ensure_pilot_reader(user, *, department="SALES"):
    """Grant a test reader through the real approval and training services."""

    read_permission = _permission("knowledge:read")
    user.role.permissions.add(read_permission)
    approver = _fixture_user(
        "knowledge-fixture-approver@example.invalid",
        "admin",
        ("knowledge:read", "knowledge:write"),
    )
    scope, _created = KnowledgeUserScope.objects.get_or_create(
        user=user,
        defaults={"department": department},
    )
    if (
        scope.department != department
        or scope.approval_status != "APPROVED"
        or not scope.pilot_enabled
    ):
        scope.department = department
        scope.approval_status = "PENDING"
        scope.pilot_enabled = False
        scope.approved_by = None
        scope.approved_at = None
        scope.training_acknowledged_at = None
        scope.save()
        PilotGovernanceService().approve_user_scope(scope.id, actor=approver)
        PilotGovernanceService().acknowledge_training(scope.id, actor=user)
    elif scope.training_acknowledged_at is None:
        PilotGovernanceService().acknowledge_training(scope.id, actor=user)
    ensure_running_pilot()
    return user


def governance_actors():
    """Return independent author and admin approver test principals."""

    author = _fixture_user(
        "knowledge-fixture-author@example.invalid",
        "knowledge-fixture-author",
        ("knowledge:read", "knowledge:write"),
    )
    approver = _fixture_user(
        "knowledge-fixture-approver@example.invalid",
        "admin",
        ("knowledge:read", "knowledge:write"),
    )
    return author, approver


def approve_and_index_existing_document(
    document,
    *,
    reader=None,
    embedding_service=None,
    release_public=False,
    department="SALES",
):
    """Complete the real review/approval/index flow for an existing draft.

    Only missing descriptive governance metadata is supplied directly because
    the production API currently has no metadata-update service. Approval,
    quality review, pilot admission, and indexing always use production
    services.
    """

    author, approver = governance_actors()
    owner = FoundationUser.objects.filter(email=document.created_by_email).first() or author
    owner.role.permissions.add(_permission("knowledge:write"))
    update_fields = []
    if not document.owner_email:
        document.owner_email = owner.email
        update_fields.append("owner_email")
    else:
        owner = FoundationUser.objects.filter(email=document.owner_email).first() or owner
        owner.role.permissions.add(_permission("knowledge:write"))
    if not document.effective_date:
        document.effective_date = timezone.localdate()
        update_fields.append("effective_date")
    if document.permission_level != "public" and not document.department:
        document.department = department
        update_fields.append("department")
    if update_fields:
        update_fields.append("updated_at")
        document.save(update_fields=update_fields)

    workflow = KnowledgeGovernanceService()
    workflow.submit_review(document.id, actor=owner)
    PilotGovernanceService().record_owner_review(document.id, actor=owner)
    workflow.approve(
        document.id,
        actor=approver,
        release_public=release_public or document.permission_level == "public",
    )
    PilotGovernanceService().record_quality_review(
        document.id,
        actor=approver,
        decision="APPROVED",
    )
    PilotGovernanceService().approve_document(document.id, actor=approver)
    KnowledgeIndexer(
        embedding_service=embedding_service or DevelopmentHashEmbeddingProvider(),
    ).reindex(document)
    document.refresh_from_db()

    if reader is not None:
        ensure_pilot_reader(reader, department=department)
    return document


def create_approved_indexed_knowledge(
    *,
    title,
    content,
    reader=None,
    permission_level="internal",
    category_name="",
    embedding_service=None,
    metadata=None,
    department="SALES",
):
    """Create and index knowledge without bypassing any governance gate."""

    author, _approver = governance_actors()
    provider = embedding_service or DevelopmentHashEmbeddingProvider()
    document = KnowledgeService(embedding_service=provider).create_document(
        title=title,
        content=content,
        category_name=category_name,
        permission_level=permission_level,
        department="" if permission_level == "public" else department,
        owner_email=author.email,
        effective_date=timezone.localdate(),
        created_by_email=author.email,
        metadata=metadata or {},
    )
    # Verify the immutable draft snapshot before invoking governance services.
    revision = document.versions.get(version=document.version)
    assert revision.content_hash == content_hash(document.content)
    return approve_and_index_existing_document(
        document,
        reader=reader,
        embedding_service=provider,
        release_public=permission_level == "public",
        department=department,
    )
