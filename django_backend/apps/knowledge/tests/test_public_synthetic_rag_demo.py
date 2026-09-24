"""Local public-widget boundary and shared synthetic RAG integration tests."""

from __future__ import annotations

import pytest

from apps.knowledge.services.public_synthetic_rag_demo import (
    PUBLIC_UNAVAILABLE_ANSWER,
    PublicSyntheticRagDemoService,
)


class _FakeRag:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def query(self, question, *, user, limit):
        self.calls.append((question, user, limit))
        return self.result


def _supported_result():
    return {
        "answer": "Housing 0011 uses SUS316. Source: [SYNTHETIC DEMO] Housing 0011",
        "status": "SUPPORTED",
        "sources": [{
            "title": "[SYNTHETIC DEMO] Housing 0011",
            "product_code": "SYN-RAG-0011",
            "citation": "synthetic://rag_synthetic_demo_v1/SYN-RAG-0011?revision=1",
            "document_id": 216,
            "chunk_id": 17893,
            "version": 1,
            "revision": "1",
            "relevance_score": 0.78,
        }],
        "retrieval": {"provider": "development-hash-fallback", "dataset_id": "rag_synthetic_demo_v1"},
    }


def test_public_output_uses_shared_rag_and_strips_internal_metadata():
    rag = _FakeRag(_supported_result())
    result = PublicSyntheticRagDemoService(rag_service=rag).answer("Find SUS316")

    assert rag.calls == [("Find SUS316", None, 3)]
    assert result == {
        "answer": "Housing 0011 uses SUS316. Source: [SYNTHETIC DEMO] Housing 0011",
        "status": "SUPPORTED",
        "sources": [{"title": "[SYNTHETIC DEMO] Housing 0011", "product_code": "SYN-RAG-0011"}],
    }
    assert "document_id" not in str(result)
    assert "synthetic://" not in str(result)


@pytest.mark.parametrize("source", [
    {"title": "Customer private quote", "product_code": "SYN-RAG-0011"},
    {"title": "[SYNTHETIC DEMO] Housing", "product_code": "REAL-0001"},
    {"title": "[SYNTHETIC DEMO] Housing", "product_code": "SYN-RAG-0011", "citation": "synthetic://other_dataset/SYN-RAG-0011"},
])
def test_public_output_fails_closed_on_non_demo_source(source):
    raw = _supported_result()
    raw["sources"] = [source]
    result = PublicSyntheticRagDemoService(rag_service=_FakeRag(raw)).answer("Find SUS316")

    assert result == {"answer": PUBLIC_UNAVAILABLE_ANSWER, "status": "UNAVAILABLE", "sources": []}


def test_public_output_fails_closed_if_generated_answer_exposes_internal_locator():
    raw = _supported_result()
    raw["answer"] += " synthetic://rag_synthetic_demo_v1/private"
    result = PublicSyntheticRagDemoService(rag_service=_FakeRag(raw)).answer("Find SUS316")

    assert result["status"] == "UNAVAILABLE"
    assert result["sources"] == []


def test_public_output_removes_relevance_score_from_generated_answer():
    raw = _supported_result()
    raw["answer"] = "Housing 0011 | relevance=0.67 uses SUS316."
    result = PublicSyntheticRagDemoService(rag_service=_FakeRag(raw)).answer("Find SUS316")

    assert result["status"] == "SUPPORTED"
    assert result["answer"] == "Housing 0011 uses SUS316."


def test_public_output_drops_verbatim_source_chunk_and_provenance():
    raw = _supported_result()
    raw["answer"] = (
        "SYNTHETIC DEMO DATA — NOT REAL COMPANY DATA\n\n"
        "Yes, Housing 0011 uses SUS316 with an electropolished finish.\n\n"
        "The relevant source is:\n\n"
        "[1] [SYNTHETIC DEMO] Housing 0011 | relevance=0.67 "
        "Provenance: dataset_id=rag_synthetic_demo_v1; production_eligible=false"
    )
    result = PublicSyntheticRagDemoService(rag_service=_FakeRag(raw)).answer("Find SUS316")

    assert result["status"] == "SUPPORTED"
    assert result["answer"] == "Yes, Housing 0011 uses SUS316 with an electropolished finish."
    assert "Provenance" not in str(result)


def test_public_output_rejects_metadata_in_answer_paragraph():
    raw = _supported_result()
    raw["answer"] = "Housing 0011 uses SUS316; dataset_id=rag_synthetic_demo_v1."
    result = PublicSyntheticRagDemoService(rag_service=_FakeRag(raw)).answer("Find SUS316")

    assert result["status"] == "UNAVAILABLE"


@pytest.mark.django_db
def test_public_endpoint_is_development_loopback_and_flag_gated(client, settings):
    url = "/api/v1/public/ai-component-demo/"
    settings.PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED = False
    settings.DEBUG = True
    assert client.get(url).status_code == 404
    settings.PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED = True
    settings.DEBUG = False
    assert client.get(url).status_code == 404
    settings.DEBUG = True
    assert client.get(url, REMOTE_ADDR="192.0.2.10").status_code == 404
    assert client.get(url).json() == {"success": True, "data": {"enabled": True}}


@pytest.mark.django_db
def test_public_endpoint_anonymous_request_is_minimal(client, settings, monkeypatch):
    settings.DEBUG = True
    settings.PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED = True
    monkeypatch.setattr(
        "apps.knowledge.views.AIGovernanceService.enforce", lambda *args, **kwargs: None,
    )
    observed = {}
    original_answer = PublicSyntheticRagDemoService.answer

    def fake_answer(self, message):
        observed["message"] = message
        return original_answer(PublicSyntheticRagDemoService(rag_service=_FakeRag(_supported_result())), message)

    monkeypatch.setattr("apps.knowledge.views.PublicSyntheticRagDemoService.answer", fake_answer)
    response = client.post(
        "/api/v1/public/ai-component-demo/",
        data={"message": "Which product uses SUS316?"},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert observed == {"message": "Which product uses SUS316?"}
    assert set(response.json()["data"]) == {"answer", "status", "sources"}


@pytest.mark.django_db
def test_public_endpoint_rejects_empty_and_long_messages(client, settings):
    settings.DEBUG = True
    settings.PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED = True
    url = "/api/v1/public/ai-component-demo/"
    for message in ("   ", "x" * 1201):
        response = client.post(url, data={"message": message}, content_type="application/json")
        assert response.status_code == 400


@pytest.mark.django_db
def test_public_endpoint_uses_governance_rate_limit(client, settings, monkeypatch):
    from apps.ai.services.governance_service import AIGovernanceError

    settings.DEBUG = True
    settings.PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED = True

    def rate_limited(*args, **kwargs):
        raise AIGovernanceError("ai_rate_limited", "AI request rate limit exceeded.", 429)

    monkeypatch.setattr("apps.knowledge.views.AIGovernanceService.enforce", rate_limited)
    response = client.post(
        "/api/v1/public/ai-component-demo/",
        data={"message": "Find SUS316"},
        content_type="application/json",
    )

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "ai_rate_limited"
