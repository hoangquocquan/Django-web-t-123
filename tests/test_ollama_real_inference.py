import pytest

from apps.ai.models import AIRequestLog
from apps.ai.services.health_service import OllamaHealthService
from apps.ai.services.ollama_client import OllamaClient, OllamaClientError, OllamaResponse
from apps.ai_agent.services.sales_assistant import SalesAssistantService
from apps.foundation.services import FoundationUserService
from apps.knowledge.services.assistant_service import KnowledgeAssistantService
from apps.knowledge.services.knowledge_service import KnowledgeService


class FakeHealthClient:
    """Fake Ollama health client with one installed model."""

    def health_check(self):
        return {
            "available": True,
            "models": ["llama3.1:latest"],
            "model_available": True,
        }


class FailingHealthClient:
    """Fake Ollama health client that simulates a local outage."""

    def health_check(self):
        raise OllamaClientError("Ollama local API is not available.")


class FakeOllamaClient:
    """Fake local model that returns a source-grounded answer."""

    model = "llama3.1"

    def generate_response(self, prompt, options=None):
        assert "Knowledge context" in prompt
        assert "CNC Capability" in prompt
        assert options["temperature"] <= 0.3
        return OllamaResponse(
            answer="CNC Capability confirms MecPrecision supports CNC shaft machining.",
            model="llama3.1",
            endpoint="http://localhost:11434",
            response_time_ms=42,
        )


class FailingOllamaClient:
    """Fake local model outage for fallback tests."""

    model = "llama3.1"

    def generate_response(self, prompt, options=None):
        raise OllamaClientError("Ollama unavailable")


class FakeSalesKnowledgeSearch:
    """Fake RAG search used by Sales Assistant."""

    def search(self, query, limit=3, user=None):
        return {
            "confidence": 0.88,
            "sources": [{"id": 1, "title": "Sales CNC Playbook", "relevance_score": 0.91}],
            "results": [],
        }


@pytest.fixture
def ai_user():
    """Create a normal admin user for AI request ownership tests."""
    return FoundationUserService().create_user(
        email="ollama-user@example.com",
        full_name="Ollama User",
        password="SecurePass123!",
        role_name="admin",
    )


def test_health_service_reports_ready_model():
    result = OllamaHealthService(client=FakeHealthClient()).check()

    assert result["status"] == "ready"
    assert result["available"] is True
    assert result["model"] == "llama3"
    assert result["model_available"] is True


def test_health_service_reports_unavailable_without_crashing():
    result = OllamaHealthService(client=FailingHealthClient()).check()

    assert result["status"] == "unavailable"
    assert result["available"] is False
    assert "Ollama local API" in result["error"]


def test_ollama_health_accepts_latest_model_suffix(monkeypatch):
    class FakeHttpResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return b'{"models":[{"name":"llama3.1:latest"}]}'

    monkeypatch.setattr("apps.ai.services.ollama_client.request.urlopen", lambda *args, **kwargs: FakeHttpResponse())

    result = OllamaClient(model="llama3.1").health_check()

    assert result["model_available"] is True


def test_ai_health_api_returns_direct_payload(client, monkeypatch):
    class FakeHealthService:
        def check(self):
            return {
                "status": "ready",
                "available": True,
                "model": "llama3.1",
                "model_available": True,
            }

    monkeypatch.setattr("apps.ai.views.OllamaHealthService", lambda: FakeHealthService())

    response = client.get("/api/v1/ai/health/")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["available"] is True


@pytest.mark.django_db
def test_rag_generation_uses_ollama_and_logs_request(ai_user):
    KnowledgeService().create_document(
        title="CNC Capability",
        content="MecPrecision supports CNC shaft machining and fixture inspection.",
        category_name="AI",
        permission_level="internal",
        created_by_email=ai_user.email,
    )

    result = KnowledgeAssistantService(ollama_client=FakeOllamaClient()).answer(
        "Does MecPrecision support CNC shaft machining?",
        user=ai_user,
    )

    assert result["generation_status"] == "generated"
    assert result["provider"] == "ollama-local"
    assert result["source_relevance_score"] > 0
    assert result["confidence"] > 0
    assert AIRequestLog.objects.count() == 1
    log = AIRequestLog.objects.first()
    assert log.model_name == "llama3.1"
    assert log.question_hash
    assert "CNC shaft" in log.question_preview
    assert log.retrieved_documents[0]["title"] == "CNC Capability"


@pytest.mark.django_db
def test_rag_generation_falls_back_when_ollama_is_down(ai_user):
    KnowledgeService().create_document(
        title="Fixture Capability",
        content="MecPrecision supports fixture design and quality inspection.",
        category_name="AI",
        permission_level="internal",
        created_by_email=ai_user.email,
    )

    result = KnowledgeAssistantService(ollama_client=FailingOllamaClient()).answer(
        "Does MecPrecision support fixture design?",
        user=ai_user,
    )

    assert result["generation_status"] == "fallback"
    assert result["provider"] == "source-fallback"
    assert "Ollama is unavailable" in result["warning"]
    assert AIRequestLog.objects.first().status == "fallback"


def test_ai_sales_assistant_returns_quality_and_human_approval():
    result = SalesAssistantService(knowledge_search=FakeSalesKnowledgeSearch()).handle(
        "lead_analysis",
        {
            "company": "Demo CNC Co",
            "contact_person": "Nguyen A",
            "industry": "CNC machining",
            "priority": "high",
            "notes": "Needs precision shaft quote.",
        },
    )

    assert result["human_approval_required"] is True
    assert result["autonomous_action"] is False
    assert result["response_quality"]["confidence"] == 0.88
    assert result["response_quality"]["source_relevance_score"] == 0.91
