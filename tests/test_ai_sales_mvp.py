import pytest
from django.test import override_settings

from apps.ai.models import AIGovernanceEvent
from apps.ai_agent import views as ai_views
from apps.ai_agent.services.sales_assistant import SalesAssistantService
from apps.business_core.models import BusinessCustomer
from apps.foundation.models import FoundationPermission, FoundationRole
from apps.foundation.services import FoundationAuthService, FoundationUserService


class DeterministicComponentRag:
    """Return one grounded synthetic component only for the supported case."""

    def query(self, question, *, user=None, limit=3):
        del user, limit
        if "sus316" not in question.casefold() or "electropolish" not in question.casefold():
            return {"status": "UNAVAILABLE", "sources": []}
        return {
            "status": "SUPPORTED",
            "sources": [
                {
                    "document_id": 11,
                    "title": "[SYNTHETIC DEMO] Electropolished sensor housing",
                    "product_code": "SYN-RAG-0011",
                    "citation": "synthetic://rag_synthetic_demo_v1/SYN-RAG-0011",
                    "version": 1,
                    "revision": "1",
                    "relevance_score": 0.95,
                }
            ],
        }


def assistant():
    return SalesAssistantService(component_rag=DeterministicComponentRag())


def supported_payload():
    return {
        "customer_name": "Synthetic Precision Systems",
        "request": "Need 100 SUS316 precision housings with CNC machining and electropolishing",
        "material": "SUS316",
        "quantity": 100,
        "process": "CNC machining",
        "surface_treatment": "electropolishing",
        "tolerance": "per customer drawing",
        "drawing_available": True,
        "deadline": "2026-12-01",
    }


def test_supported_sales_case_is_grounded_and_human_reviewed():
    result = assistant().analyze(supported_payload())

    assert result["status"] == "SUPPORTED"
    assert result["priority"] == "HIGH"
    assert result["priority_reasons"]
    assert result["matched_products"][0]["product_code"] == "SYN-RAG-0011"
    assert result["sources"][0]["citation"].startswith("synthetic://")
    assert result["recommended_next_action"] == "REVIEW_PRODUCT_MATCH"
    assert result["human_approval_required"] is True
    assert result["autonomous_action"] is False


def test_weather_request_is_unavailable_without_sales_recommendation():
    result = assistant().analyze({"request": "What is the weather in Tokyo?"})

    assert result["status"] == "UNAVAILABLE"
    assert result["matched_products"] == []
    assert result["sources"] == []
    assert result["recommended_next_action"] == "NO_ACTION"


def test_incomplete_request_asks_for_missing_information():
    result = assistant().analyze({"request": "Need precision component."})

    assert result["status"] == "NEEDS_MORE_INFORMATION"
    assert result["priority"] == "NEEDS_REVIEW"
    assert "requested material" in result["missing_information"]
    assert "manufacturing process" in result["missing_information"]
    assert result["recommended_next_action"] == "REQUEST_TECHNICAL_DETAILS"


def _grant_internal_ai_sales(role_name):
    role, _created = FoundationRole.objects.get_or_create(name=role_name)
    for module in ("ai_sales", "sales"):
        permission, _created = FoundationPermission.objects.get_or_create(
            code=f"{module}:read",
            defaults={"module": module, "action": "read"},
        )
        role.permissions.add(permission)
    return role


def _user(role_name, email):
    _grant_internal_ai_sales(role_name)
    return FoundationUserService().create_user(
        email=email,
        full_name=role_name.title(),
        password="SecurePass123!",
        role_name=role_name,
    )


def _headers(user):
    token, _row = FoundationAuthService().login(user.email, "SecurePass123!")
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.mark.django_db
def test_internal_endpoint_denies_anonymous_and_viewer(client):
    viewer = FoundationUserService().create_user(
        email="ai-sales-viewer@example.com",
        full_name="AI Sales Viewer",
        password="SecurePass123!",
        role_name="viewer",
    )

    anonymous = client.post(
        "/api/v1/internal/ai-sales/analyze/",
        data=supported_payload(),
        content_type="application/json",
    )
    denied_viewer = client.post(
        "/api/v1/internal/ai-sales/analyze/",
        data=supported_payload(),
        content_type="application/json",
        **_headers(viewer),
    )

    assert anonymous.status_code == 403
    assert denied_viewer.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("role_name", ["sales", "manager", "admin"])
def test_internal_endpoint_allows_governed_sales_roles_and_audits(
    client, monkeypatch, role_name
):
    user = _user(role_name, f"ai-sales-{role_name}@example.com")
    monkeypatch.setattr(
        ai_views,
        "SalesAssistantService",
        lambda: assistant(),
    )

    response = client.post(
        "/api/v1/internal/ai-sales/analyze/",
        data=supported_payload(),
        content_type="application/json",
        **_headers(user),
    )

    assert response.status_code == 200
    result = response.json()["data"]
    assert result["status"] == "SUPPORTED"
    assert result["request_id"]
    event = AIGovernanceEvent.objects.get(correlation_id=result["request_id"])
    assert event.user_email == user.email
    assert event.metadata == {
        "input_reference": "synthetic:ad-hoc",
        "result_status": "SUPPORTED",
        "source_ids": [11],
    }


@pytest.mark.django_db
@override_settings(PUBLIC_AI_ENABLED=False, PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED=False)
def test_private_sales_data_cannot_surface_through_public_component_endpoint(client):
    BusinessCustomer.objects.create(
        company_name="PRIVATE SALES CUSTOMER 9f82",
        contact_name="Private Contact",
        notes="Secret RFQ for SUS316 electropolishing",
    )

    response = client.post(
        "/api/v1/public/ai-component-demo/",
        data={"message": "Tell me about PRIVATE SALES CUSTOMER 9f82"},
        content_type="application/json",
    )

    assert response.status_code == 404
    assert b"PRIVATE SALES CUSTOMER 9f82" not in response.content
