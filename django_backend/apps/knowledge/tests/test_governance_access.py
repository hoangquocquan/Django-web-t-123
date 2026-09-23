"""Synthetic, isolated governance and RAG authorization regression tests."""

from __future__ import annotations

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
import io
from django.utils import timezone
from datetime import timedelta

from apps.business_core.models import BusinessCustomer
from apps.foundation.models import FoundationAuthToken, FoundationPermission, FoundationRole, FoundationUser
from apps.foundation.services import FoundationAuthService
from apps.knowledge.models import (
    DocumentPermission, KnowledgeAuditEvent, KnowledgeChunk, KnowledgePilotProgram,
    KnowledgeUserScope,
)
from apps.knowledge.services.access_policy import KnowledgeAccessPolicy
from apps.knowledge.services.business_connector import BusinessKnowledgeConnector
from apps.knowledge.services.embedding_service import DevelopmentHashEmbeddingProvider
from apps.knowledge.services.governance import KnowledgeGovernanceService
from apps.knowledge.services.knowledge_indexer import KnowledgeIndexer
from apps.knowledge.services.knowledge_service import KnowledgeService
from apps.knowledge.services.pilot_governance import PilotGovernanceService
from apps.knowledge.services.search_service import KnowledgeSearchService
from apps.knowledge.services.assistant_service import KnowledgeAssistantService
from apps.knowledge.services.public_assistant_service import PublicKnowledgeAssistantService


@pytest.fixture
def actors():
    KnowledgePilotProgram.objects.create(
        name="FIRST_INTERNAL_AI_PILOT", status="RUNNING",
        planned_start=timezone.localdate() - timedelta(days=1),
        planned_end=timezone.localdate() + timedelta(days=14),
    )
    read, _ = FoundationPermission.objects.get_or_create(code="knowledge:read", defaults={"module": "knowledge", "action": "read"})
    write, _ = FoundationPermission.objects.get_or_create(code="knowledge:write", defaults={"module": "knowledge", "action": "write"})
    customer, _ = FoundationPermission.objects.get_or_create(code="customer:view", defaults={"module": "customer", "action": "view"})
    ai_sales, _ = FoundationPermission.objects.get_or_create(code="ai_sales:read", defaults={"module": "ai_sales", "action": "read"})
    admin, _ = FoundationRole.objects.get_or_create(name="admin")
    worker, _ = FoundationRole.objects.get_or_create(name="knowledge-test-employee")
    admin.permissions.add(read, write)
    worker.permissions.add(read, write, customer, ai_sales)
    admin.permissions.add(ai_sales)
    users = {
        "admin": FoundationUser.objects.create(email="approver@example.invalid", full_name="Approver", password_hash="!", role=admin),
        "author": FoundationUser.objects.create(email="author@example.invalid", full_name="Author", password_hash="!", role=worker),
        "other": FoundationUser.objects.create(email="other@example.invalid", full_name="Other", password_hash="!", role=worker),
    }
    for user in users.values():
        KnowledgeUserScope.objects.create(
            user=user, department="SALES", pilot_enabled=True,
            approval_status="APPROVED", approved_at=timezone.now(),
            training_acknowledged_at=timezone.now(),
        )
    return users


def draft(*, level="internal", author, department="SALES"):
    return KnowledgeService().create_document(
        title="Synthetic governance source", content="Synthetic machining accuracy section",
        permission_level=level, department=department, created_by_email=author.email,
        owner_email=author.email, effective_date=timezone.now().date(),
    )


def approved(document, approver, *, release_public=False):
    workflow = KnowledgeGovernanceService()
    workflow.submit_review(document.id, actor=approver)
    owner = FoundationUser.objects.get(email=document.owner_email)
    PilotGovernanceService().record_owner_review(document.id, actor=owner)
    workflow.approve(document.id, actor=approver, release_public=release_public)
    PilotGovernanceService().record_quality_review(
        document.id, actor=approver, decision="APPROVED",
    )
    return PilotGovernanceService().approve_document(document.id, actor=approver)


@pytest.mark.django_db
def test_draft_cannot_embed_and_creation_is_unindexed(actors):
    document = draft(author=actors["author"])
    assert document.status == "DRAFT"
    assert not KnowledgeChunk.objects.filter(document=document).exists()
    with pytest.raises(PermissionDenied):
        KnowledgeIndexer(embedding_service=DevelopmentHashEmbeddingProvider()).reindex(document)
    assert KnowledgeAuditEvent.objects.filter(event="indexed").count() == 0
    output = io.StringIO()
    call_command("reindex_knowledge_embeddings", stdout=output)
    assert "processed=0 skipped=1 failed=0" in output.getvalue()


@pytest.mark.django_db
def test_approval_requires_independent_admin_and_exact_revision(actors):
    document = draft(author=actors["author"])
    workflow = KnowledgeGovernanceService()
    workflow.submit_review(document.id, actor=actors["author"])
    PilotGovernanceService().record_owner_review(document.id, actor=actors["author"])
    with pytest.raises(PermissionDenied):
        workflow.approve(document.id, actor=actors["author"])
    document.content = "Changed since draft snapshot"
    document.save(update_fields=["content"])
    with pytest.raises(ValidationError):
        workflow.approve(document.id, actor=actors["admin"])
    document.refresh_from_db()
    assert document.status == "REVIEW"


@pytest.mark.django_db
def test_approved_current_index_binds_revision_and_citation(actors):
    document = draft(author=actors["author"])
    approved(document, actors["admin"])
    KnowledgeIndexer(embedding_service=DevelopmentHashEmbeddingProvider()).reindex(document)
    result = KnowledgeSearchService(embedding_service=DevelopmentHashEmbeddingProvider()).search(
        "machining accuracy", user=actors["author"],
    )
    assert result["sources"]
    source = result["sources"][0]
    assert source["version"] == 1
    assert source["revision_id"] == document.versions.get(version=1).id
    assert source["revision_date"]
    assert "section" in source and "page" in source
    assert result["results"][0]["chunk"]["revision_id"] == source["revision_id"]
    assert KnowledgeAuditEvent.objects.filter(event="approved", document=document).exists()
    assert KnowledgeAuditEvent.objects.filter(event="indexed", document=document).exists()
    assert KnowledgeAuditEvent.objects.filter(event="query", source_ids=[document.id]).exists()


@pytest.mark.django_db
def test_archived_document_is_removed_from_list_search_and_raw_service(actors):
    document = draft(author=actors["author"])
    approved(document, actors["admin"])
    KnowledgeIndexer(embedding_service=DevelopmentHashEmbeddingProvider()).reindex(document)
    KnowledgeGovernanceService().archive(document.id, actor=actors["admin"])
    assert not KnowledgeAccessPolicy().eligible_documents(actors["author"]).filter(id=document.id).exists()
    assert KnowledgeSearchService(embedding_service=DevelopmentHashEmbeddingProvider()).search(
        "machining accuracy", user=actors["author"],
    )["sources"] == []
    assert KnowledgeService(embedding_service=DevelopmentHashEmbeddingProvider()).search(
        "machining accuracy", user=actors["author"],
    ) == []
    assert KnowledgeAuditEvent.objects.filter(event="archived", document=document).exists()


@pytest.mark.django_db
def test_public_internal_and_restricted_use_same_policy_before_vector_scoring(actors, client):
    internal = draft(author=actors["author"])
    restricted = draft(level="restricted", author=actors["author"])
    public = draft(level="public", author=actors["author"])
    for doc in (internal, restricted):
        approved(doc, actors["admin"])
        KnowledgeIndexer(embedding_service=DevelopmentHashEmbeddingProvider()).reindex(doc)
    approved(public, actors["admin"], release_public=True)
    KnowledgeIndexer(embedding_service=DevelopmentHashEmbeddingProvider()).reindex(public)
    policy = KnowledgeAccessPolicy()
    assert set(policy.eligible_documents(None).values_list("id", flat=True)) == {public.id}
    assert set(policy.eligible_documents(actors["author"]).values_list("id", flat=True)) == {internal.id, public.id}
    assert not policy.can_read(restricted, actors["author"])

    class SpyVector:
        def search(self, *, queryset, **kwargs):
            assert {chunk.document_id for chunk in queryset} == {internal.id, public.id}
            return []

    result = KnowledgeSearchService(
        embedding_service=DevelopmentHashEmbeddingProvider(), vector_store=SpyVector(),
    ).search("unrelated", user=actors["author"])
    assert restricted.id not in {source["id"] for source in result["sources"]}
    assert client.post("/api/v1/public/ai/assistant/", {"question": "hello"}).status_code == 404
    with pytest.raises(PermissionDenied):
        PublicKnowledgeAssistantService().answer("hello")

    DocumentPermission.objects.create(document=restricted, role_name=actors["author"].role.name, can_read=True)
    assert policy.can_read(restricted, actors["author"])
    DocumentPermission.objects.create(document=restricted, user_email=actors["author"].email, can_read=False)
    assert not policy.can_read(restricted, actors["author"])


@pytest.mark.django_db
def test_public_label_without_release_or_current_revision_is_denied(actors):
    document = draft(level="public", author=actors["author"])
    workflow = KnowledgeGovernanceService()
    workflow.submit_review(document.id, actor=actors["author"])
    PilotGovernanceService().record_owner_review(document.id, actor=actors["author"])
    with pytest.raises(ValidationError):
        workflow.approve(document.id, actor=actors["admin"])
    assert not KnowledgeAccessPolicy().eligible_documents(None).filter(pk=document.pk).exists()
    workflow.approve(document.id, actor=actors["admin"], release_public=True)
    document.version = 2
    document.save(update_fields=["version"])
    assert not KnowledgeAccessPolicy().eligible_documents(None).filter(pk=document.pk).exists()
    with pytest.raises(PermissionDenied):
        KnowledgeIndexer(embedding_service=DevelopmentHashEmbeddingProvider()).reindex(document)


@pytest.mark.django_db
def test_business_connector_only_returns_explicit_owned_rows_and_logs_denials(actors):
    own = BusinessCustomer.objects.create(contact_name="Own", company_name="Own Co", email="private@example.invalid", created_by=actors["author"])
    foreign = BusinessCustomer.objects.create(contact_name="Other", company_name="Other Co", created_by=actors["other"])
    connector = BusinessKnowledgeConnector()
    assert connector.build_context("all customers", user=actors["author"]) == {}
    context = connector.build_context("all customers", user=actors["author"], customer_id=own.id)
    assert context["customer"]["company_name"] == "Own Co"
    assert "email" not in context["customer"]
    with pytest.raises(PermissionDenied):
        connector.build_context("all customers", user=actors["author"], customer_id=foreign.id)
    with pytest.raises(PermissionDenied):
        connector.build_context("all customers", customer_id=own.id)
    assert KnowledgeAuditEvent.objects.filter(event="denied").count() == 2


@pytest.mark.django_db
def test_transition_api_requires_writer_and_separate_approver(actors, client):
    document = draft(author=actors["author"])

    def auth(user):
        raw = f"synthetic-{user.id}"
        FoundationAuthToken.objects.get_or_create(
            token_hash=FoundationAuthService.hash_token(raw),
            defaults={"user": user, "expires_at": timezone.now() + timedelta(hours=1)},
        )
        return {"HTTP_AUTHORIZATION": f"Bearer {raw}"}

    review_url = f"/api/v1/knowledge/documents/{document.id}/review/"
    approve_url = f"/api/v1/knowledge/documents/{document.id}/approve/"
    owner_review_url = f"/api/v1/knowledge/documents/{document.id}/owner-review/"
    assert client.post(review_url).status_code == 403
    assert client.post(review_url, **auth(actors["author"])).status_code == 200
    assert client.post(owner_review_url, **auth(actors["author"])).status_code == 200
    assert client.post(approve_url, data="{}", content_type="application/json", **auth(actors["author"])).status_code == 403
    assert client.post(approve_url, data="{}", content_type="application/json", **auth(actors["admin"])).status_code == 200
    assert document.id not in KnowledgeAccessPolicy().eligible_documents(actors["author"]).values_list("id", flat=True)
    PilotGovernanceService().record_quality_review(
        document.id, actor=actors["admin"], decision="APPROVED",
    )
    PilotGovernanceService().approve_document(document.id, actor=actors["admin"])
    assert document.id in KnowledgeAccessPolicy().eligible_documents(actors["author"]).values_list("id", flat=True)


@pytest.mark.django_db
def test_generation_revocation_suppresses_answer_and_citation(actors, monkeypatch):
    document = draft(author=actors["author"])
    approved(document, actors["admin"])
    KnowledgeIndexer(embedding_service=DevelopmentHashEmbeddingProvider()).reindex(document)

    class RevokingGeneration:
        def __init__(self, **kwargs):
            pass

        def generate(self, question, retrieval, **kwargs):
            KnowledgeGovernanceService().archive(document.id, actor=actors["admin"])
            return {
                "answer": "Unsafe stale answer", "warning": "", "confidence": 0.9,
                "model": "test", "response_time_ms": 0, "generation_status": "generated",
                "source_relevance_score": 0.9, "hallucination_warning": "",
            }

    monkeypatch.setattr("apps.knowledge.services.assistant_service.RagGenerationPipeline", RevokingGeneration)
    result = KnowledgeAssistantService(
        search_service=KnowledgeSearchService(embedding_service=DevelopmentHashEmbeddingProvider()),
    ).answer("machining accuracy", user=actors["author"])
    assert result["generation_status"] == "blocked_revoked"
    assert result["sources"] == []
    assert "Unsafe stale answer" not in result["answer"]

