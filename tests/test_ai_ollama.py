import json
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from apps.ai.services.ollama_client import OllamaClient, OllamaClientError, OllamaResponse
from apps.ai.services.prompt_manager import PromptManager
from apps.foundation.models import FoundationRole
from apps.foundation.services import FoundationAuthService, FoundationUserService


class FakeHttpResponse:
    """Small context manager that behaves like urllib's response object."""

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class FakeOllamaClient:
    """Predictable Ollama client double for API tests."""

    def generate_response(self, prompt):
        assert "Xin chao" in prompt
        return OllamaResponse(
            answer="Xin chao, day la cau tra loi tu Ollama local.",
            model="test-model",
            endpoint="http://localhost:11434",
        )


class FailingOllamaClient:
    """Ollama client double that simulates a local service outage."""

    def generate_response(self, prompt):
        raise OllamaClientError("Ollama local API is not available.")


@pytest.fixture
def foundation_user():
    """Create an admin user that can call the AI endpoint."""
    return FoundationUserService().create_user(
        email="ai-admin@example.com",
        full_name="AI Admin",
        password="SecurePass123!",
        role_name="admin",
    )


@pytest.fixture
def viewer_user():
    """Create a viewer user that should not have AI write permission."""
    return FoundationUserService().create_user(
        email="ai-viewer@example.com",
        full_name="AI Viewer",
        password="SecurePass123!",
        role_name="viewer",
    )


def bearer_header(user):
    """Create a Bearer token header for a foundation user."""
    token, _token_row = FoundationAuthService().login(user.email, "SecurePass123!")
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def test_prompt_manager_rejects_empty_message():
    with pytest.raises(ValidationError):
        PromptManager().prepare_chat_prompt("   ")


def test_prompt_manager_builds_system_and_user_prompt():
    prompt = PromptManager().prepare_chat_prompt("MecPrecision co gia cong CNC khong?")

    assert "MecPrecision VIETNAM" in prompt.combined
    assert "MecPrecision co gia cong CNC khong?" in prompt.combined


def test_ollama_health_check_reads_local_models():
    payload = {"models": [{"name": "llama3.1"}, {"name": "qwen2.5"}]}
    with patch(
        "apps.ai.services.ollama_client.request.urlopen",
        return_value=FakeHttpResponse(payload),
    ):
        result = OllamaClient(model="llama3.1").health_check()

    assert result["available"] is True
    assert result["model_available"] is True
    assert "qwen2.5" in result["models"]


def test_ollama_generate_response_returns_answer():
    payload = {"response": "AI local response"}
    with patch(
        "apps.ai.services.ollama_client.request.urlopen",
        return_value=FakeHttpResponse(payload),
    ):
        result = OllamaClient(model="llama3.1").generate_response("Hello")

    assert result.answer == "AI local response"
    assert result.model == "llama3.1"


def test_ollama_generate_response_handles_empty_answer():
    with patch(
        "apps.ai.services.ollama_client.request.urlopen",
        return_value=FakeHttpResponse({"response": ""}),
    ):
        with pytest.raises(OllamaClientError):
            OllamaClient(retries=0).generate_response("Hello")


@pytest.mark.django_db
def test_ai_chat_api_requires_authentication(client):
    response = client.post(
        "/api/v1/ai/chat/",
        data={"message": "Xin chao"},
        content_type="application/json",
    )

    assert response.status_code == 403
    assert response.json()["success"] is False


@pytest.mark.django_db
def test_ai_chat_api_requires_permission(client, viewer_user):
    response = client.post(
        "/api/v1/ai/chat/",
        data={"message": "Xin chao"},
        content_type="application/json",
        **bearer_header(viewer_user),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


@pytest.mark.django_db
def test_ai_chat_api_returns_ollama_answer(client, foundation_user):
    with patch("apps.ai.views.OllamaClient", return_value=FakeOllamaClient()):
        response = client.post(
            "/api/v1/ai/chat/",
            data={"message": "Xin chao"},
            content_type="application/json",
            **bearer_header(foundation_user),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["answer"] == "Xin chao, day la cau tra loi tu Ollama local."
    assert body["data"]["provider"] == "ollama-local"


@pytest.mark.django_db
def test_ai_chat_api_returns_service_unavailable_when_ollama_is_down(client, foundation_user):
    with patch("apps.ai.views.OllamaClient", return_value=FailingOllamaClient()):
        response = client.post(
            "/api/v1/ai/chat/",
            data={"message": "Xin chao"},
            content_type="application/json",
            **bearer_header(foundation_user),
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ollama_unavailable"
