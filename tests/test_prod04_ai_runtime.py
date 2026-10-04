"""Focused production-safety tests for PROD-04 AI runtime controls."""

import json
from pathlib import Path
from typing import ClassVar

import pytest
from apps.ai.services.model_config import (
    AIModelConfigService,
    AIModelConfigurationError,
)
from apps.ai.services.ollama_client import OllamaClient, OllamaClientError
from apps.ai.services.runtime_capacity import AIRuntimeBusyError, AIRuntimeCapacity
from apps.ai.views import AiChatRequestSerializer
from apps.ai_agent.services.tools import ToolRegistry
from apps.knowledge.models import KnowledgeChunk, KnowledgeDocument, KnowledgeEmbedding
from apps.knowledge.services.runtime_health import KnowledgeRuntimeHealthService
from django.test import override_settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SharedCapacityBackend:
    """Tiny shared backend double that exposes multi-worker capacity behavior."""

    active: ClassVar[set[tuple[str, str]]] = set()

    def acquire(self, key, token, limit, lease_ms, now_ms):
        if len(self.active) >= limit:
            return False
        self.active.add((key, token))
        return True

    def release(self, key, token):
        self.active.discard((key, token))


class FakeHealth:
    def __init__(self, payload):
        self.payload = payload

    def check(self):
        return self.payload


class FakeEmbedding:
    provider_name = "ollama-local"
    model_name = "nomic-embed-text"
    dimensions = 1
    embedding_version = "v1"

    def health_check(self):
        return {"available": True, "model_available": True, "model": self.model_name}


class FakeVectorStore:
    def health_check(self):
        return {"available": True, "backend": "test-vector", "production_ready": True}


class FakeIndexer:
    def needs_reindex(self, document):
        return False


def test_model_allowlist_is_owned_by_server_settings():
    with override_settings(
        OLLAMA_MODEL="llama3",
        OLLAMA_GENERATION_MODELS=("llama3", "qwen2.5"),
    ):
        service = AIModelConfigService()
        assert service.validate_model("llama3:latest") == "llama3:latest"
        with pytest.raises(AIModelConfigurationError, match="not approved"):
            service.validate_model("untrusted-model")


def test_ollama_rejects_external_endpoint_and_unapproved_model():
    with pytest.raises(OllamaClientError, match="approved local"):
        OllamaClient(host="https://external-ai.example")
    with (
        override_settings(OLLAMA_GENERATION_MODELS=("llama3",)),
        pytest.raises(OllamaClientError, match="not approved"),
    ):
        OllamaClient(model="untrusted-model")


def test_capacity_is_shared_and_released_across_workers():
    backend = SharedCapacityBackend()
    backend.active.clear()
    worker_a = AIRuntimeCapacity(
        backend=backend, limit=1, lease_seconds=10, clock=lambda: 1
    )
    worker_b = AIRuntimeCapacity(
        backend=backend, limit=1, lease_seconds=10, clock=lambda: 1
    )
    with worker_a.slot(), pytest.raises(AIRuntimeBusyError), worker_b.slot():
        pass
    with worker_b.slot():
        assert len(backend.active) == 1
    assert not backend.active


@pytest.mark.django_db
def test_rag_health_reports_empty_index_as_degraded():
    result = KnowledgeRuntimeHealthService(
        ollama_health=FakeHealth(
            {"status": "ready", "model_available": True, "endpoint_reachable": True}
        ),
        embedding_provider=FakeEmbedding(),
        vector_store=FakeVectorStore(),
        indexer=FakeIndexer(),
    ).check()
    assert result["status"] == "degraded"
    assert result["index"]["coverage"] == 1.0
    assert result["index"]["stale_document_ids"] == []


@pytest.mark.django_db
def test_rag_health_reports_populated_index_as_ready():
    document = KnowledgeDocument.objects.create(title="Runtime", content="CNC")
    chunk = KnowledgeChunk.objects.create(document=document, content="CNC")
    KnowledgeEmbedding.objects.create(
        chunk=chunk,
        vector=[1.0],
        provider="ollama-local",
        model_name="nomic-embed-text",
        dimension=1,
    )
    result = KnowledgeRuntimeHealthService(
        ollama_health=FakeHealth({"status": "ready", "model_available": True}),
        embedding_provider=FakeEmbedding(),
        vector_store=FakeVectorStore(),
        indexer=FakeIndexer(),
    ).check()
    assert result["status"] == "ready"
    assert result["index"]["coverage"] == 1.0


@pytest.mark.django_db
def test_rag_health_endpoint_requires_permission(client):
    assert client.get("/api/v1/knowledge/health/").status_code == 403


def test_agent_registry_contains_only_explicit_read_only_tools():
    definitions = ToolRegistry().list_tools()
    assert definitions
    assert all(item["read_only"] is True for item in definitions)
    forbidden = {"shell", "sql", "database_write", "deploy", "send_email"}
    assert forbidden.isdisjoint(item["name"] for item in definitions)


def test_n8n_workflow_has_auth_retry_correlation_and_human_gate():
    workflow = json.loads(
        (PROJECT_ROOT / "n8n" / "workflows" / "prod04_ai_runtime_gate.json").read_text(
            encoding="utf-8"
        )
    )
    nodes = {node["name"]: node for node in workflow["nodes"]}
    validation = nodes["Validate Signature And Safety Gates"]["parameters"]["jsCode"]
    result = nodes["Build Safe Result"]["parameters"]["jsCode"]
    health = nodes["Verify Django Health"]
    assert "createHmac('sha256'" in validation
    assert "timingSafeEqual" in validation
    assert "correlation_id" in validation
    assert "human_approval_required === true" in validation
    assert "auto_merge === false" in validation
    assert "auto_deploy === false" in validation
    assert "approval_bypass_detected === false" in validation
    assert health["retryOnFail"] is True and health["maxTries"] == 3
    assert "phase_advanced: false" in result
    assert "human_approval_required: true" in result


def test_n8n_error_workflow_fails_closed_without_external_action():
    workflow = json.loads(
        (PROJECT_ROOT / "n8n" / "workflows" / "prod04_error_workflow.json").read_text(
            encoding="utf-8"
        )
    )
    node_types = {node["type"] for node in workflow["nodes"]}
    rendered = json.dumps(workflow)
    assert "n8n-nodes-base.errorTrigger" in node_types
    assert "httpRequest" not in rendered
    assert "executeCommand" not in rendered
    assert "auto_merge: false" in rendered
    assert "auto_deploy: false" in rendered


def test_clients_cannot_supply_a_model_field_to_ai_chat():
    serializer = AiChatRequestSerializer(
        data={"message": "hello", "model": "untrusted-model"}
    )
    assert serializer.is_valid()
    assert serializer.validated_data == {"message": "hello"}
