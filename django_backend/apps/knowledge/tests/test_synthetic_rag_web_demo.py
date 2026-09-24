"""API, grounding, and isolation tests for the internal synthetic RAG demo."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.foundation.models import FoundationAuthToken, FoundationRole, FoundationUser
from apps.foundation.services import FoundationAuthService
from apps.knowledge.models import KnowledgeDocument
from apps.knowledge.services.synthetic_rag_demo import (
    DATASET_ID, SyntheticRagPromptTemplate, SyntheticRagWebDemoService,
    create_and_index_knowledge, import_products,
)
from apps.knowledge.tests.test_synthetic_rag_demo import synthetic_row


def _user_token(role_name, suffix):
    role = FoundationRole.objects.get(name=role_name)
    user = FoundationUser.objects.create(
        email=f"rag-web-{suffix}@example.invalid",
        full_name=f"RAG Web {suffix}",
        password_hash="test-only",
        role=role,
    )
    token = f"rag-web-token-{suffix}"
    FoundationAuthToken.objects.create(
        user=user,
        token_hash=FoundationAuthService.hash_token(token),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    return user, token


def _headers(token):
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.mark.django_db
def test_anonymous_and_viewer_are_denied(client):
    anonymous = client.post(
        "/api/v1/internal/rag-demo/query/",
        data={"question": "Find SYN-RAG-0001"},
        content_type="application/json",
    )
    _viewer, viewer_token = _user_token("viewer", "viewer")
    viewer = client.post(
        "/api/v1/internal/rag-demo/query/",
        data={"question": "Find SYN-RAG-0001"},
        content_type="application/json",
        **_headers(viewer_token),
    )

    assert anonymous.status_code == 403
    assert viewer.status_code == 403


@pytest.mark.django_db
def test_authorized_internal_request_succeeds(client, monkeypatch):
    _user, token = _user_token("admin", "admin")
    monkeypatch.setattr(
        "apps.knowledge.views.AIGovernanceService.enforce", lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "apps.knowledge.views.SyntheticRagWebDemoService.query",
        lambda self, question, user, limit: {
            "answer": "Grounded synthetic answer",
            "status": "SUPPORTED",
            "sources": [{"product_code": "SYN-RAG-0001", "citation": "synthetic://rag_synthetic_demo_v1/SYN-RAG-0001?revision=1"}],
            "retrieval": {"result_count": 1, "provider": "development-hash-fallback", "dataset_id": DATASET_ID},
        },
    )

    response = client.post(
        "/api/v1/internal/rag-demo/query/",
        data={"question": "Find SYN-RAG-0001"},
        content_type="application/json",
        **_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "SUPPORTED"
    assert response.json()["data"]["sources"][0]["product_code"] == "SYN-RAG-0001"


class _FakeGenerationPipeline:
    def generate(self, question, retrieval, user=None, fallback_builder=None):
        del question, user, fallback_builder
        title = retrieval["sources"][0]["title"]
        return {
            "answer": f"SYNTHETIC DEMO DATA — NOT REAL COMPANY DATA\n\nSource: {title}",
            "confidence": retrieval["confidence"],
            "provider": "source-fallback",
            "generation_status": "fallback",
        }


@pytest.mark.django_db
def test_supported_query_returns_citation_and_strict_synthetic_filter(settings):
    settings.KNOWLEDGE_EMBEDDING_PROVIDER = "development-hash"
    row = synthetic_row()
    imported = import_products([row])
    create_and_index_knowledge([row], imported["product_ids"])
    KnowledgeDocument.objects.create(
        title="Customer quotation secret",
        content="Customer Alpha RFQ price and order margin.",
        source_type="text",
        permission_level="internal",
        status="INDEXED",
        metadata={"synthetic": False, "production_eligible": True},
    )

    result = SyntheticRagWebDemoService(
        generation_pipeline=_FakeGenerationPipeline(),
    ).query("What synthetic technical record is identified by SYN-RAG-0001?")

    assert result["status"] == "SUPPORTED"
    assert result["sources"]
    assert {source["product_code"] for source in result["sources"]} == {"SYN-RAG-0001"}
    assert all(source["citation"].startswith(f"synthetic://{DATASET_ID}/") for source in result["sources"])
    assert "Customer quotation" not in result["answer"]


@pytest.mark.django_db
def test_unsupported_commercial_question_returns_unavailable(settings):
    settings.KNOWLEDGE_EMBEDDING_PROVIDER = "development-hash"
    row = synthetic_row()
    imported = import_products([row])
    create_and_index_knowledge([row], imported["product_ids"])

    result = SyntheticRagWebDemoService(
        generation_pipeline=_FakeGenerationPipeline(),
    ).query("What is the sales price of SYN-RAG-0001?")

    assert result["status"] == "UNAVAILABLE"
    assert result["sources"] == []
    assert "does not contain this information" in result["answer"]


@pytest.mark.django_db
def test_internal_chat_endpoint_reuses_scoped_service(client, monkeypatch):
    _user, token = _user_token("admin", "chat-admin")
    monkeypatch.setattr(
        "apps.knowledge.views.AIGovernanceService.enforce", lambda *args, **kwargs: None,
    )
    observed = {}

    def fake_query(self, question, user, limit):
        observed.update(question=question, user=user.email, limit=limit)
        return {
            "answer": "Grounded chat answer",
            "status": "SUPPORTED",
            "sources": [{"product_code": "SYN-RAG-0011"}],
            "retrieval": {"dataset_id": DATASET_ID},
        }

    monkeypatch.setattr(
        "apps.knowledge.views.SyntheticRagWebDemoService.query", fake_query,
    )
    response = client.post(
        "/api/v1/internal/rag-chat/",
        data={"message": "Which product uses SUS316?"},
        content_type="application/json",
        **_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["data"]["question"] == "Which product uses SUS316?"
    assert response.json()["data"]["sources"][0]["product_code"] == "SYN-RAG-0011"
    assert observed == {
        "question": "Which product uses SUS316?",
        "user": "rag-web-chat-admin@example.invalid",
        "limit": 3,
    }


@pytest.mark.django_db
def test_internal_chat_rejects_anonymous_empty_and_long_input(client):
    anonymous = client.post(
        "/api/v1/internal/rag-chat/",
        data={"message": "Find SYN-RAG-0011"},
        content_type="application/json",
    )
    _user, token = _user_token("admin", "chat-validation")
    empty = client.post(
        "/api/v1/internal/rag-chat/",
        data={"message": "   "},
        content_type="application/json",
        **_headers(token),
    )
    long_message = client.post(
        "/api/v1/internal/rag-chat/",
        data={"message": "x" * 1201},
        content_type="application/json",
        **_headers(token),
    )

    assert anonymous.status_code == 403
    assert empty.status_code == 400
    assert long_message.status_code == 400


@pytest.mark.django_db
def test_internal_chat_rejects_viewer_and_internal_user_without_knowledge_read(client):
    _viewer, viewer_token = _user_token("viewer", "chat-viewer")
    _sales, sales_token = _user_token("Sales", "chat-no-permission")
    FoundationRole.objects.get(name="Sales").permissions.clear()

    viewer = client.post(
        "/api/v1/internal/rag-chat/",
        data={"message": "Find SYN-RAG-0011"},
        content_type="application/json",
        **_headers(viewer_token),
    )
    no_permission = client.post(
        "/api/v1/internal/rag-chat/",
        data={"message": "Find SYN-RAG-0011"},
        content_type="application/json",
        **_headers(sales_token),
    )

    assert viewer.status_code == 403
    assert no_permission.status_code == 403


def test_synthetic_prompt_treats_demo_records_as_grounded_not_missing():
    prompt = SyntheticRagPromptTemplate().build(
        "Find the bronze bushing.",
        {"knowledge_context": "[1] Bushing 0015: oil impregnated bronze"},
    )

    assert "authoritative inside this demo" in prompt
    assert "Answer only with facts explicitly present" in prompt
    assert "price, customer, stock" in prompt
