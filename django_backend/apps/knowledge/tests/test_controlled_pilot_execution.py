"""Phase 8B.2 approval, feedback, evaluation, and monitoring controls."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.foundation.models import (
    FoundationAuthToken, FoundationPermission, FoundationRole, FoundationUser,
)
from apps.foundation.services import FoundationAuthService
from apps.knowledge.models import (
    KnowledgeAssistantFeedback, KnowledgeAssistantLog, KnowledgeAuditEvent,
    KnowledgeGapReview, KnowledgeHumanEvaluation, KnowledgePilotProgram,
    KnowledgeUserScope,
)
from apps.knowledge.services.access_policy import KnowledgeAccessPolicy
from apps.knowledge.services.governance import KnowledgeGovernanceService
from apps.knowledge.services.knowledge_service import KnowledgeService
from apps.knowledge.services.knowledge_indexer import KnowledgeIndexer
from apps.knowledge.services.pilot_governance import PilotGovernanceService
from apps.knowledge.services.pilot_batch_ingestion import PilotBatchIngestionService
from apps.knowledge.services.pilot_program import PilotProgramService


def _permission(code):
    module, action = code.split(":", 1)
    return FoundationPermission.objects.get_or_create(
        code=code, defaults={"module": module, "action": action},
    )[0]


def _token(user):
    raw = f"phase8b2-{user.id}"
    FoundationAuthToken.objects.get_or_create(
        token_hash=FoundationAuthService.hash_token(raw),
        defaults={
            "user": user,
            "expires_at": timezone.now() + timedelta(hours=1),
        },
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {raw}"}


@pytest.fixture
def pilot_actors(db):
    KnowledgePilotProgram.objects.create(
        name="FIRST_INTERNAL_AI_PILOT", status="RUNNING",
        planned_start=timezone.localdate(),
        planned_end=timezone.localdate() + timedelta(days=14),
    )
    read, write = _permission("knowledge:read"), _permission("knowledge:write")
    admin_role, _ = FoundationRole.objects.get_or_create(name="admin")
    sales_role, _ = FoundationRole.objects.get_or_create(name="Phase8B2 Sales")
    management_role, _ = FoundationRole.objects.get_or_create(name="Phase8B2 Management")
    admin_role.permissions.add(read, write)
    sales_role.permissions.add(read)
    management_role.permissions.add(read, write)
    admin = FoundationUser.objects.create(
        email="phase8b2-approver@example.invalid", full_name="Approver",
        password_hash="!", role=admin_role,
    )
    author = FoundationUser.objects.create(
        email="phase8b2-author@example.invalid", full_name="Author",
        password_hash="!", role=admin_role,
    )
    sales = FoundationUser.objects.create(
        email="phase8b2-sales@example.invalid", full_name="Sales Pilot",
        password_hash="!", role=sales_role,
    )
    reviewer = FoundationUser.objects.create(
        email="phase8b2-reviewer@example.invalid", full_name="Management Reviewer",
        password_hash="!", role=management_role,
    )
    sales_scope = KnowledgeUserScope.objects.create(user=sales, department="SALES")
    reviewer_scope = KnowledgeUserScope.objects.create(user=reviewer, department="MANAGEMENT")
    return {
        "admin": admin, "author": author, "sales": sales, "reviewer": reviewer,
        "sales_scope": sales_scope, "reviewer_scope": reviewer_scope,
    }


@pytest.mark.django_db
def test_user_and_document_require_separate_explicit_pilot_approvals(pilot_actors):
    actors = pilot_actors
    document = KnowledgeService().create_document(
        title="Approved Sales FAQ", content="Approved sales intake workflow.",
        permission_level="internal", department="SALES",
        created_by_email=actors["author"].email,
        owner_email=actors["author"].email,
        effective_date=timezone.now().date(),
    )
    governance = KnowledgeGovernanceService()
    governance.submit_review(document.id, actor=actors["author"])
    PilotGovernanceService().record_owner_review(document.id, actor=actors["author"])
    governance.approve(document.id, actor=actors["admin"])

    assert not KnowledgeAccessPolicy().eligible_documents(actors["sales"]).exists()
    PilotGovernanceService().approve_user_scope(
        actors["sales_scope"].id, actor=actors["admin"],
        expires_at=timezone.now() + timedelta(days=30),
    )
    PilotGovernanceService().acknowledge_training(
        actors["sales_scope"].id, actor=actors["sales"],
    )
    assert not KnowledgeAccessPolicy().eligible_documents(actors["sales"]).exists()
    PilotGovernanceService().record_quality_review(
        document.id, actor=actors["admin"], decision="APPROVED",
    )
    PilotGovernanceService().approve_document(document.id, actor=actors["admin"])
    loaded = PilotBatchIngestionService().load([document.id], actor=actors["admin"])
    assert loaded["loaded_count"] == 1
    assert loaded["documents"][0]["document_id"] == document.id
    assert loaded["documents"][0]["chunk_count"] >= 1
    assert KnowledgeAccessPolicy().eligible_documents(actors["sales"]).filter(pk=document.id).exists()


@pytest.mark.django_db
def test_sensitive_or_incomplete_document_is_blocked_from_pilot(pilot_actors):
    actors = pilot_actors
    sensitive = KnowledgeService().create_document(
        title="Unsafe data", content="Customer confidential cost and margin details.",
        permission_level="internal", department="SALES",
        created_by_email=actors["author"].email,
        owner_email=actors["author"].email,
        effective_date=timezone.now().date(),
    )
    governance = KnowledgeGovernanceService()
    governance.submit_review(sensitive.id, actor=actors["author"])
    PilotGovernanceService().record_owner_review(sensitive.id, actor=actors["author"])
    governance.approve(sensitive.id, actor=actors["admin"])
    with pytest.raises(ValidationError):
        PilotGovernanceService().record_quality_review(
            sensitive.id, actor=actors["admin"], decision="APPROVED",
        )
    PilotGovernanceService().record_quality_review(
        sensitive.id, actor=actors["admin"], decision="REJECTED",
        rejection_reason="CONFIDENTIAL",
    )
    with pytest.raises(ValidationError):
        PilotGovernanceService().approve_document(sensitive.id, actor=actors["admin"])
    sensitive.refresh_from_db()
    assert not sensitive.pilot_corpus_approved
    assert sensitive.quality_review_status == "REJECTED"


@pytest.mark.django_db
def test_missing_or_wrong_owner_cannot_approve_or_index(pilot_actors):
    actors = pilot_actors
    document = KnowledgeService().create_document(
        title="Ownerless FAQ", content="Synthetic FAQ content.",
        permission_level="internal", department="SALES",
        created_by_email=actors["author"].email,
        effective_date=timezone.now().date(),
    )
    governance = KnowledgeGovernanceService()
    governance.submit_review(document.id, actor=actors["author"])
    with pytest.raises(ValidationError):
        PilotGovernanceService().record_owner_review(document.id, actor=actors["author"])
    with pytest.raises(ValidationError):
        governance.approve(document.id, actor=actors["admin"])
    with pytest.raises(PermissionDenied):
        KnowledgeIndexer().reindex(document)

    document.owner_email = actors["sales"].email
    document.save(update_fields=["owner_email"])
    with pytest.raises(PermissionDenied):
        PilotGovernanceService().record_owner_review(document.id, actor=actors["author"])


@pytest.mark.django_db
def test_real_pilot_launch_is_blocked_without_minimum_corpus_and_cohort(pilot_actors):
    actors = pilot_actors
    KnowledgePilotProgram.objects.filter(name="FIRST_INTERNAL_AI_PILOT").update(status="DRAFT")
    service = PilotProgramService()
    readiness = service.readiness()
    assert readiness["corpus_count"] == 0
    assert readiness["corpus_ready"] is False
    assert readiness["users_ready"] is False
    with pytest.raises(ValidationError):
        service.launch(
            actor=actors["admin"], planned_start=timezone.localdate(),
            planned_end=timezone.localdate() + timedelta(days=14),
        )
    assert not service.is_running()
    with pytest.raises(ValidationError):
        PilotBatchIngestionService().load([], actor=actors["admin"])
    with pytest.raises(ValidationError):
        PilotBatchIngestionService().load(list(range(1, 27)), actor=actors["admin"])


@pytest.mark.django_db
def test_feedback_evaluation_and_monitoring_store_no_answer_content(client, pilot_actors):
    actors = pilot_actors
    service = PilotGovernanceService()
    service.approve_user_scope(actors["sales_scope"].id, actor=actors["admin"])
    service.approve_user_scope(actors["reviewer_scope"].id, actor=actors["admin"])
    service.acknowledge_training(actors["sales_scope"].id, actor=actors["sales"])
    service.acknowledge_training(actors["reviewer_scope"].id, actor=actors["reviewer"])
    interaction = KnowledgeAssistantLog.objects.create(
        question="", answer="", sources=[{"id": 7, "version": 1}],
        confidence=0.8, user_email=actors["sales"].email,
    )
    KnowledgeAuditEvent.objects.create(
        event="query", actor_id=actors["sales"].id, decision="allowed", source_ids=[7],
    )

    feedback = client.post(
        "/api/v1/knowledge/feedback/",
        data={"interaction_id": interaction.id, "category": "MISSING_SOURCE"},
        content_type="application/json", **_token(actors["sales"]),
    )
    evaluation = client.post(
        "/api/v1/knowledge/human-evaluation/",
        data={
            "interaction_id": interaction.id, "rating": "PARTIALLY_CORRECT",
            "question_category": "RFQ", "permission_correct": True,
            "citation_valid": False, "missing_information": True,
            "hallucination": False,
        },
        content_type="application/json", **_token(actors["reviewer"]),
    )
    gap = client.post(
        "/api/v1/knowledge/gap-review/",
        data={
            "interaction_id": interaction.id,
            "category": "MISSING_DOCUMENT", "resolved": False,
        },
        content_type="application/json", **_token(actors["reviewer"]),
    )
    monitoring = client.get(
        "/api/v1/knowledge/pilot/monitoring/", **_token(actors["reviewer"]),
    )

    assert feedback.status_code == 200
    assert evaluation.status_code == 200
    assert gap.status_code == 200
    assert monitoring.status_code == 200
    assert KnowledgeAssistantFeedback.objects.get().category == "MISSING_SOURCE"
    assert KnowledgeHumanEvaluation.objects.get().rating == "PARTIALLY_CORRECT"
    assert KnowledgeGapReview.objects.get().category == "MISSING_DOCUMENT"
    payload = monitoring.json()["data"]
    assert payload["queries"] == 1
    assert payload["top_document_ids"] == [{"document_id": 7, "uses": 1}]
    assert payload["feedback"]["MISSING_SOURCE"] == 1
    assert payload["knowledge_gaps"]["MISSING_DOCUMENT"] == 1
    assert "answer" not in str(payload).lower()


@pytest.mark.django_db
def test_sales_user_cannot_submit_management_evaluation(client, pilot_actors):
    actors = pilot_actors
    PilotGovernanceService().approve_user_scope(
        actors["sales_scope"].id, actor=actors["admin"]
    )
    PilotGovernanceService().acknowledge_training(
        actors["sales_scope"].id, actor=actors["sales"]
    )
    interaction = KnowledgeAssistantLog.objects.create(
        question="", answer="", user_email=actors["sales"].email,
    )
    response = client.post(
        "/api/v1/knowledge/human-evaluation/",
        data={
            "interaction_id": interaction.id, "rating": "CORRECT",
            "question_category": "PRODUCT", "permission_correct": True,
            "citation_valid": True,
        },
        content_type="application/json", **_token(actors["sales"]),
    )
    assert response.status_code == 403
    assert not KnowledgeHumanEvaluation.objects.exists()
