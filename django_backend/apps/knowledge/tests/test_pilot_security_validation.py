"""Phase 8B validation of current fail-closed internal chat boundaries."""

from __future__ import annotations

import pytest
from datetime import timedelta
from django.utils import timezone

from apps.foundation.models import (
    FoundationAuthToken, FoundationPermission, FoundationRole, FoundationUser,
)
from apps.foundation.services import FoundationAuthService
from apps.knowledge.models import (
    DocumentPermission, KnowledgeAssistantLog, KnowledgeAuditEvent, KnowledgePilotProgram,
    KnowledgeUserScope,
)
from apps.knowledge.services.assistant_service import KnowledgeAssistantService
from apps.knowledge.services.embedding_service import DevelopmentHashEmbeddingProvider
from apps.knowledge.services.governance import KnowledgeGovernanceService
from apps.knowledge.services.knowledge_indexer import KnowledgeIndexer
from apps.knowledge.services.knowledge_service import KnowledgeService
from apps.knowledge.services.pilot_governance import PilotGovernanceService
from apps.knowledge.services.search_service import KnowledgeSearchService


@pytest.fixture(autouse=True)
def running_synthetic_pilot(db):
    KnowledgePilotProgram.objects.create(
        name="FIRST_INTERNAL_AI_PILOT", status="RUNNING",
        planned_start=timezone.localdate(),
        planned_end=timezone.localdate() + timedelta(days=14),
    )


@pytest.mark.django_db
def test_draft_source_cannot_generate_an_internal_answer():
    read, _ = FoundationPermission.objects.get_or_create(
        code="knowledge:read", defaults={"module": "knowledge", "action": "read"},
    )
    role, _ = FoundationRole.objects.get_or_create(name="Sales")
    role.permissions.add(read)
    user = FoundationUser.objects.create(
        email="sales-pilot@example.invalid", full_name="Sales Pilot", password_hash="!", role=role,
    )
    KnowledgeUserScope.objects.create(
        user=user, department="SALES", pilot_enabled=True,
        approval_status="APPROVED", approved_at=timezone.now(),
        training_acknowledged_at=timezone.now(),
    )
    draft = KnowledgeService().create_document(
        title="Synthetic RFQ guideline", content="Never publish draft RFQ instructions",
        permission_level="internal", department="SALES", created_by_email=user.email,
    )

    class NoModelCall:
        model = "synthetic-no-call"

        def generate_response(self, *args, **kwargs):
            raise AssertionError("The model must not run without an approved source.")

    result = KnowledgeAssistantService(
        search_service=KnowledgeSearchService(embedding_service=DevelopmentHashEmbeddingProvider()),
        ollama_client=NoModelCall(),
    ).answer("RFQ guideline", user=user)

    assert result["generation_status"] == "blocked_no_context"
    assert result["sources"] == []
    assert draft.id not in [source["id"] for source in result["sources"]]
    assert KnowledgeAuditEvent.objects.filter(event="query", decision="denied", source_ids=[]).exists()
    log = KnowledgeAssistantLog.objects.latest("id")
    assert log.question == "" and log.answer == "" and log.sources == []


def _permission(code):
    module, action = code.split(":", 1)
    return FoundationPermission.objects.get_or_create(
        code=code, defaults={"module": module, "action": action},
    )[0]


def _auth(user):
    raw = f"pilot-token-{user.id}"
    FoundationAuthToken.objects.create(
        user=user, token_hash=FoundationAuthService.hash_token(raw),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {raw}"}


@pytest.mark.django_db
def test_department_scope_filters_before_retrieval_and_explicit_grant_is_narrow():
    read = _permission("knowledge:read")
    write = _permission("knowledge:write")
    admin_role, _ = FoundationRole.objects.get_or_create(name="admin")
    sales_role, _ = FoundationRole.objects.get_or_create(name="Sales")
    engineering_role, _ = FoundationRole.objects.get_or_create(name="Engineering")
    admin_role.permissions.add(read, write)
    sales_role.permissions.add(read)
    engineering_role.permissions.add(read)
    approver = FoundationUser.objects.create(email="pilot-approver@example.invalid", full_name="Approver", password_hash="!", role=admin_role)
    author = FoundationUser.objects.create(email="pilot-author@example.invalid", full_name="Author", password_hash="!", role=admin_role)
    sales = FoundationUser.objects.create(email="pilot-sales@example.invalid", full_name="Sales", password_hash="!", role=sales_role)
    engineer = FoundationUser.objects.create(email="pilot-engineer@example.invalid", full_name="Engineer", password_hash="!", role=engineering_role)
    KnowledgeUserScope.objects.create(user=sales, department="SALES", pilot_enabled=True, approval_status="APPROVED", approved_at=timezone.now(), training_acknowledged_at=timezone.now())
    KnowledgeUserScope.objects.create(user=engineer, department="ENGINEERING", pilot_enabled=True, approval_status="APPROVED", approved_at=timezone.now(), training_acknowledged_at=timezone.now())

    docs = []
    for title, department, content in [
        ("Sales RFQ", "SALES", "rfq intake quantity material drawing"),
        ("Engineering Technical", "ENGINEERING", "technical spindle geometry process"),
    ]:
        doc = KnowledgeService().create_document(
            title=title, content=content, permission_level="internal",
            department=department, created_by_email=author.email,
            owner_email=author.email, effective_date=timezone.now().date(),
        )
        governance = KnowledgeGovernanceService()
        governance.submit_review(doc.id, actor=author)
        PilotGovernanceService().record_owner_review(doc.id, actor=author)
        governance.approve(doc.id, actor=approver)
        PilotGovernanceService().record_quality_review(
            doc.id, actor=approver, decision="APPROVED",
        )
        PilotGovernanceService().approve_document(doc.id, actor=approver)
        KnowledgeIndexer(embedding_service=DevelopmentHashEmbeddingProvider()).reindex(doc)
        docs.append(doc)

    class SalesVectorSpy:
        def search(self, *, queryset, **kwargs):
            assert {chunk.document_id for chunk in queryset} == {docs[0].id}
            return []

    KnowledgeSearchService(
        embedding_service=DevelopmentHashEmbeddingProvider(), vector_store=SalesVectorSpy(),
    ).search("technical rfq", user=sales)
    sales_ids = set(KnowledgeService().list_documents(sales).values_list("id", flat=True))
    engineering_ids = set(KnowledgeService().list_documents(engineer).values_list("id", flat=True))
    assert sales_ids == {docs[0].id}
    assert engineering_ids == {docs[1].id}

    DocumentPermission.objects.create(document=docs[1], user_email=sales.email, can_read=True)
    assert set(KnowledgeService().list_documents(sales).values_list("id", flat=True)) == {docs[0].id, docs[1].id}


@pytest.mark.django_db
def test_disabled_pilot_user_gets_no_internal_or_public_knowledge():
    read = _permission("knowledge:read")
    role, _ = FoundationRole.objects.get_or_create(name="Disabled Pilot")
    role.permissions.add(read)
    user = FoundationUser.objects.create(email="disabled-pilot@example.invalid", full_name="Disabled", password_hash="!", role=role)
    KnowledgeUserScope.objects.create(user=user, department="SALES", pilot_enabled=False)
    assert not KnowledgeService().list_documents(user).exists()


@pytest.mark.django_db
def test_non_pilot_user_cannot_call_internal_chat(client):
    read = _permission("knowledge:read")
    role, _ = FoundationRole.objects.get_or_create(name="Not Enabled")
    role.permissions.add(read)
    user = FoundationUser.objects.create(email="not-enabled@example.invalid", full_name="No Pilot", password_hash="!", role=role)
    headers = _auth(user)
    chat = client.post(
        "/api/v1/knowledge/chat/", data={"question": "RFQ?"},
        content_type="application/json", **headers,
    )
    assert chat.status_code == 403
    assert KnowledgeAuditEvent.objects.filter(event="denied", actor_id=user.id).count() == 1
