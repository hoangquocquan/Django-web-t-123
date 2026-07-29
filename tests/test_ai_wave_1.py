import json
from pathlib import Path

import pytest

from apps.ai_agent.models import AgentRun
from apps.ai_agent.services.agent_controller import AgentController, ExecutionPlanner
from apps.ai_agent.services.tools import ToolRegistry
from apps.foundation.services import FoundationAuthService, FoundationUserService
from apps.knowledge.models import KnowledgeDocument, KnowledgeEmbedding
from apps.knowledge.services.embedding_service import LocalEmbeddingService
from apps.knowledge.services.knowledge_service import KnowledgeService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def admin_user():
    """Create a user with wildcard admin permissions."""
    return FoundationUserService().create_user(
        email="ai-wave-admin@example.com",
        full_name="AI Wave Admin",
        password="SecurePass123!",
        role_name="admin",
    )


@pytest.fixture
def viewer_user():
    """Create a user that can read knowledge but cannot run agent write flows."""
    return FoundationUserService().create_user(
        email="ai-wave-viewer@example.com",
        full_name="AI Wave Viewer",
        password="SecurePass123!",
        role_name="viewer",
    )


def bearer_header(user):
    """Return a Django foundation Bearer token header."""
    token, _token_row = FoundationAuthService().login(user.email, "SecurePass123!")
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.mark.django_db
def test_rag_ingests_document_chunks_and_embeddings():
    document = KnowledgeService().ingest_text(
        title="CNC Capability",
        content="MecPrecision provides CNC machining, precision shafts, and fixture manufacturing.",
        source_type="markdown",
    )

    assert KnowledgeDocument.objects.count() == 1
    assert document.chunks.count() >= 1
    assert KnowledgeEmbedding.objects.count() == document.chunks.count()


@pytest.mark.django_db
def test_rag_semantic_search_returns_relevant_documents():
    KnowledgeService().ingest_text(
        title="Fixture Manufacturing",
        content="Fixture and jig manufacturing for CNC inspection and production.",
    )

    results = KnowledgeService().search("CNC fixture", limit=3)

    assert results
    assert results[0]["chunk"].document.title == "Fixture Manufacturing"


def test_embedding_is_deterministic_and_normalized():
    service = LocalEmbeddingService()
    first = service.embed("CNC fixture")
    second = service.embed("CNC fixture")

    assert first == second
    assert len(first) == service.dimensions
    assert service.similarity(first, second) > 0.99


@pytest.mark.django_db
def test_knowledge_search_api_requires_authentication(client):
    response = client.post(
        "/api/v1/knowledge/search/",
        data={"query": "CNC"},
        content_type="application/json",
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


@pytest.mark.django_db
def test_knowledge_search_api_returns_results(client, viewer_user):
    KnowledgeService().ingest_text(
        title="Precision Shaft",
        content="Precision shaft machining with CNC turning and strict tolerance control.",
    )

    response = client.post(
        "/api/v1/knowledge/search/",
        data={"query": "shaft CNC", "limit": 2},
        content_type="application/json",
        **bearer_header(viewer_user),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["results"]


def test_agent_planner_selects_expected_tools():
    tools = ExecutionPlanner().plan("Give me monthly sales report and database count")

    assert "database_summary" in tools
    assert "report_generator" in tools


def test_tool_registry_lists_safe_tools():
    tool_names = {tool["name"] for tool in ToolRegistry().list_tools()}

    assert {"knowledge_search", "database_summary", "report_generator", "system_information"}.issubset(tool_names)


@pytest.mark.django_db
def test_agent_controller_executes_tools_and_records_run(admin_user):
    KnowledgeService().ingest_text(
        title="Product Knowledge",
        content="MecPrecision manufactures CNC products and inspection fixtures.",
    )

    result = AgentController().run("Create product knowledge report", user=admin_user)

    assert result["run_id"]
    assert AgentRun.objects.count() == 1
    assert "knowledge_search" in AgentRun.objects.first().selected_tools
    assert result["tool_results"]


@pytest.mark.django_db
def test_agent_api_requires_write_permission(client, viewer_user):
    response = client.post(
        "/api/v1/agent/run/",
        data={"request": "Create report"},
        content_type="application/json",
        **bearer_header(viewer_user),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


@pytest.mark.django_db
def test_agent_api_runs_for_admin(client, admin_user):
    response = client.post(
        "/api/v1/agent/run/",
        data={"request": "Create system report"},
        content_type="application/json",
        **bearer_header(admin_user),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["run_id"]
    assert "system_information" in [item["tool"] for item in body["data"]["tool_results"]]


def test_n8n_local_workflow_is_documented_and_inactive():
    workflow_path = PROJECT_ROOT / "n8n" / "workflows" / "ai_contact_classification.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))

    assert workflow["active"] is False
    assert "Django AI Classify" in {node["name"] for node in workflow["nodes"]}


def test_ai_factory_v2_documents_exist():
    required = [
        PROJECT_ROOT / "docs" / "ai" / "RAG_ARCHITECTURE.md",
        PROJECT_ROOT / "docs" / "ai" / "RAG_USAGE.md",
        PROJECT_ROOT / "docs" / "ai" / "AI_AGENT_ARCHITECTURE.md",
        PROJECT_ROOT / "docs" / "ai" / "N8N_AI_AUTOMATION.md",
        PROJECT_ROOT / "docs" / "ai" / "AI_FACTORY_V2_ARCHITECTURE.md",
        PROJECT_ROOT / "ai-factory" / "evidence" / "ai_wave_1_complete.json",
    ]

    for path in required:
        assert path.exists()
        assert path.stat().st_size > 0
