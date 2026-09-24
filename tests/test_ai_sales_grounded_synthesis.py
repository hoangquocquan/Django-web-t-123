import json
from pathlib import Path

import pytest
from django.test import override_settings

from apps.ai.services.ollama_client import OllamaClientError, OllamaResponse
from apps.ai_agent.services.sales_assistant import SalesAssistantService
from apps.ai_agent.services import sales_synthesis
from apps.ai_agent.services.sales_synthesis import GroundedSalesSynthesisService


def valid_output(source_ids=None):
    """Return one response that satisfies the AI Sales output contract."""
    return {
        "summary": "The lead fits MEC Precision's documented CNC capability.",
        "reasoning_summary": ["The request mentions precision CNC work."],
        "recommended_next_steps": ["Ask a human engineer to review the drawing."],
        "draft_email": {"subject": "CNC drawing review", "body": "Please share the drawing for human review."},
        "risks": ["Tolerance details are not yet available."],
        "source_ids": source_ids or [11],
        "human_approval_required": True,
        "autonomous_action": False,
    }


def grounded_facts():
    """Create facts with one real source ID for isolated synthesis tests."""
    return {
        "lead_facts": {"company": "Precision Demo", "contact_person": "Lan", "notes": "CNC shaft"},
        "score_facts": {"score": 85, "grade": "A", "factors": ["technical_fit:+15"]},
        "crm_facts": {},
        "sales_facts": {"action": "lead_analysis"},
        "knowledge_sources": [{"id": 11, "title": "CNC capability", "excerpt": "CNC shaft machining"}],
    }


class FakeOllamaClient:
    """Provide deterministic Ollama outcomes without network access."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)

    def generate_response(self, _prompt, response_format=None):
        assert response_format == "json"
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return OllamaResponse(answer=outcome, model="test-model", endpoint="local", response_time_ms=7)


@override_settings(AI_SALES_OLLAMA_ENABLED=True)
def test_valid_json_uses_ollama_and_preserves_source_contract():
    service = GroundedSalesSynthesisService(
        client=FakeOllamaClient([json.dumps(valid_output())]),
        max_attempts=1,
    )

    result = service.synthesize(grounded_facts())

    assert result["generation_mode"] == "ollama"
    assert result["source_ids"] == [11]
    assert "score" not in result
    assert result["human_approval_required"] is True
    assert result["autonomous_action"] is False


@pytest.mark.parametrize(
    "model_output,expected_error",
    [
        ("not-json", "not valid JSON"),
        (json.dumps({"summary": "missing fields"}), "Missing required fields"),
        (json.dumps(valid_output([999])), "unknown knowledge source"),
        (json.dumps({**valid_output(), "lead_score": 99}), "cannot return or modify"),
    ],
)
@override_settings(AI_SALES_OLLAMA_ENABLED=True)
def test_invalid_or_hallucinated_output_uses_explicit_fallback(model_output, expected_error):
    service = GroundedSalesSynthesisService(client=FakeOllamaClient([model_output]), max_attempts=1)

    result = service.synthesize(grounded_facts())

    assert result["generation_mode"] == "fallback"
    assert expected_error in result["validation_errors"][0]
    assert result["source_ids"] == [11]


@override_settings(AI_SALES_OLLAMA_ENABLED=True)
def test_dangerous_autonomous_output_is_blocked():
    dangerous = valid_output()
    dangerous["summary"] = "CRM updated and email sent"
    service = GroundedSalesSynthesisService(client=FakeOllamaClient([json.dumps(dangerous)]), max_attempts=1)

    result = service.synthesize(grounded_facts())

    assert result["generation_mode"] == "fallback"
    assert "prohibited autonomous action" in result["validation_errors"][0]
    assert result["autonomous_action"] is False


@override_settings(AI_SALES_OLLAMA_ENABLED=True)
def test_hallucinated_pipeline_status_is_blocked():
    hallucinated = valid_output()
    hallucinated["summary"] = "MEC Precision won the lead."
    service = GroundedSalesSynthesisService(client=FakeOllamaClient([json.dumps(hallucinated)]), max_attempts=1)

    result = service.synthesize(grounded_facts())

    assert result["generation_mode"] == "fallback"
    assert "contradicts deterministic lead status" in result["validation_errors"][0]


@override_settings(AI_SALES_OLLAMA_ENABLED=True)
def test_ollama_offline_retries_then_uses_deterministic_fallback():
    service = GroundedSalesSynthesisService(
        client=FakeOllamaClient([OllamaClientError("offline"), OllamaClientError("offline")]),
        max_attempts=2,
    )

    result = service.synthesize(grounded_facts(), task="email_draft")

    assert result["generation_mode"] == "fallback"
    assert result["model"] == ""
    assert result["human_approval_required"] is True
    assert result["draft_email"]["subject"]


@override_settings(AI_SALES_OLLAMA_ENABLED=True)
def test_invalid_first_response_can_be_repaired_with_bounded_retry():
    service = GroundedSalesSynthesisService(
        client=FakeOllamaClient(["invalid", json.dumps(valid_output())]),
        max_attempts=2,
    )

    result = service.synthesize(grounded_facts())

    assert result["generation_mode"] == "ollama"
    assert result["validation_errors"] == []


class FakeKnowledgeSearch:
    """Return a small grounded knowledge result for assistant integration tests."""

    def search(self, _query, limit=3, user=None):
        return {
            "confidence": 0.8,
            "sources": [{"id": 11, "title": "CNC capability", "relevance_score": 0.8}],
            "results": [
                {
                    "document": {"id": 11},
                    "chunk": {"content": "MEC Precision machines precision CNC shafts."},
                }
            ],
        }


class FakeSynthesis:
    """Return safe synthesis so deterministic assistant behavior can be inspected."""

    def synthesize(self, _facts, task="lead_analysis"):
        return {**valid_output(), "generation_mode": "ollama", "model": "test", "response_time_ms": 1}


def test_model_cannot_change_deterministic_lead_score():
    service = SalesAssistantService(
        knowledge_search=FakeKnowledgeSearch(),
        synthesis_service=FakeSynthesis(),
    )

    result = service.handle(
        "lead_analysis",
        {
            "company": "CNC Demo",
            "contact_person": "Lan",
            "industry": "CNC",
            "priority": "high",
            "notes": "precision shaft",
        },
    )

    assert result["score"] == 83
    assert "score" not in result["synthesis"]
    assert result["facts"]["score_facts"]["score"] == result["score"]


def test_email_is_always_a_draft_and_never_auto_sent():
    service = SalesAssistantService(
        knowledge_search=FakeKnowledgeSearch(),
        synthesis_service=FakeSynthesis(),
    )

    result = service.handle(
        "email_draft",
        {"company": "Demo Co", "contact_person": "An", "product_interest": "CNC shaft"},
    )

    assert result["delivery_status"] == "draft_only_not_sent"
    assert result["human_approval_required"] is True
    assert result["autonomous_action"] is False
    assert result["draft"]["subject"]


@override_settings(AI_SALES_OLLAMA_ENABLED=True)
def test_failure_log_does_not_contain_prompt_or_pii(monkeypatch):
    facts = grounded_facts()
    facts["lead_facts"]["notes"] = "Contact secret.person@example.com"
    logged = []
    monkeypatch.setattr(sales_synthesis.logger, "warning", lambda *args: logged.append(args))
    service = GroundedSalesSynthesisService(
        client=FakeOllamaClient([OllamaClientError("offline")]),
        max_attempts=1,
    )

    service.synthesize(facts)

    rendered_log = " ".join(str(value) for call in logged for value in call)
    assert "secret.person@example.com" not in rendered_log
    assert "offline" in rendered_log


def test_business_ui_renders_structured_cards_instead_of_raw_dictionary():
    template = Path("django_backend/apps/business_ui/templates/business_ui/ai_sales.html").read_text(encoding="utf-8")

    assert "result.synthesis.summary" in template
    assert "result.synthesis.draft_email.subject" in template
    assert "<pre>{{ result }}</pre>" not in template
