import pytest
from datetime import date
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from apps.ai.models import AIGovernanceEvent
from apps.ai_agent import views as ai_views
from apps.ai_agent.services.sales_assistant import SalesAssistantService
from apps.ai_agent.services.ai_sales_knowledge import AISalesKnowledgeSourceService
from apps.ai_agent.services.ai_sales_metrics import AISalesMetricsService
from apps.business_core.models import BusinessCustomer, BusinessMaterial
from apps.foundation.models import FoundationPermission, FoundationRole
from apps.foundation.services import FoundationAuthService, FoundationUserService
from apps.sales.models import SalesRfq, SalesRfqLine


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


class CapturingComponentRag(DeterministicComponentRag):
    def __init__(self):
        self.question = ""

    def query(self, question, *, user=None, limit=3):
        self.question = question
        return super().query(question, user=user, limit=limit)


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
    rag = CapturingComponentRag()
    result = SalesAssistantService(component_rag=rag).analyze(supported_payload())

    assert result["status"] == "SUPPORTED"
    assert result["priority"] == "HIGH"
    assert result["priority_reasons"]
    assert result["matched_products"][0]["product_code"] == "SYN-RAG-0011"
    assert result["sources"][0]["citation"].startswith("synthetic://")
    assert result["recommended_next_action"] == "REVIEW_PRODUCT_MATCH"
    assert result["human_approval_required"] is True
    assert result["autonomous_action"] is False
    assert rag.question == "SUS316 CNC machining electropolishing"
    assert "Synthetic Precision Systems" not in rag.question


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


@pytest.mark.django_db
def test_persisted_rfq_context_uses_canonical_business_ids():
    user = _user("admin", "ai-sales-rfq-admin@example.com")
    customer = BusinessCustomer.objects.create(
        company_name="Canonical RFQ Customer",
        contact_name="Buyer",
    )
    material = BusinessMaterial.objects.create(
        material_code="SUS316",
        name="Stainless steel",
        grade="SUS316",
        created_by=user,
    )
    rfq = SalesRfq.objects.create(
        rfq_number="RFQ-AI-SALES-001",
        customer=customer,
        project_name="Electropolished precision housing",
        quote_due_at=date(2026, 11, 1),
        required_delivery_date=date(2026, 12, 1),
        created_by=user,
    )
    SalesRfqLine.objects.create(
        rfq=rfq,
        line_number=1,
        material=material,
        description="SUS316 precision housing",
        quantity=100,
        required_delivery_date=date(2026, 12, 1),
        tolerance="per drawing",
        technical_notes="CNC machining and electropolishing",
        drawing_required=True,
    )

    result = assistant().analyze({"rfq_id": rfq.id}, user=user)

    assert result["status"] == "SUPPORTED"
    assert result["input_reference"] == f"rfq:{rfq.id}"
    assert result["synthetic_input"] is False
    assert result["matched_products"][0]["product_code"] == "SYN-RAG-0011"
    assert result["human_approval_required"] is True


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
    anonymous_selector = client.get("/api/v1/internal/ai-sales/rfqs/")
    denied_viewer_selector = client.get(
        "/api/v1/internal/ai-sales/rfqs/", **_headers(viewer)
    )

    assert anonymous.status_code == 403
    assert denied_viewer.status_code == 403
    assert anonymous_selector.status_code == 403
    assert denied_viewer_selector.status_code == 403


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
    assert event.metadata["input_reference"] == "synthetic:ad-hoc"
    assert event.metadata["result_status"] == "SUPPORTED"
    assert event.metadata["priority"] == "HIGH"
    assert event.metadata["source_ids"] == [11]
    assert event.metadata["retrieval"] == "hit"
    assert event.metadata["provider"] == "fallback"
    assert event.metadata["deterministic_fallback"] is True
    assert event.metadata["latency_ms"] >= 0
    assert "Synthetic Precision Systems" not in str(event.metadata)


@pytest.mark.django_db
def test_rfq_selector_and_analysis_enforce_sales_object_scope(client, monkeypatch):
    sales_user = _user("sales", "ai-sales-owner@example.com")
    other_sales = _user("sales", "ai-sales-other@example.com")
    customer = BusinessCustomer.objects.create(
        company_name="Scoped Customer",
        contact_name="Private Buyer",
        email="private-buyer@example.com",
        notes="Do not expose this private note in the selector.",
    )
    owned = SalesRfq.objects.create(
        rfq_number="RFQ-SCOPE-OWNED",
        customer=customer,
        project_name="Owned project",
        notes="Owned private RFQ note",
        quote_due_at=date(2026, 11, 1),
        required_delivery_date=date(2026, 12, 1),
        created_by=sales_user,
    )
    assigned = SalesRfq.objects.create(
        rfq_number="RFQ-SCOPE-ASSIGNED",
        customer=customer,
        project_name="Assigned project",
        notes="Assigned private RFQ note",
        quote_due_at=date(2026, 11, 2),
        required_delivery_date=date(2026, 12, 2),
        created_by=other_sales,
        assigned_to=sales_user,
    )
    foreign = SalesRfq.objects.create(
        rfq_number="RFQ-SCOPE-FOREIGN",
        customer=customer,
        project_name="Foreign project",
        notes="Foreign secret RFQ note",
        quote_due_at=date(2026, 11, 3),
        required_delivery_date=date(2026, 12, 3),
        created_by=other_sales,
    )

    selector = client.get(
        "/api/v1/internal/ai-sales/rfqs/", **_headers(sales_user)
    )
    assert selector.status_code == 200
    payload = selector.json()["data"]
    assert {item["id"] for item in payload["results"]} == {owned.id, assigned.id}
    assert foreign.id not in {item["id"] for item in payload["results"]}
    serialized = str(payload)
    assert "private-buyer@example.com" not in serialized
    assert "private RFQ note" not in serialized

    monkeypatch.setattr(ai_views, "SalesAssistantService", lambda: assistant())
    denied = client.post(
        "/api/v1/internal/ai-sales/analyze/",
        data={"rfq_id": foreign.id},
        content_type="application/json",
        **_headers(sales_user),
    )
    assert denied.status_code == 404
    assert "RFQ-SCOPE-FOREIGN" not in denied.content.decode()
    assert "Foreign secret RFQ note" not in denied.content.decode()


@pytest.mark.django_db
def test_manager_selector_can_review_all_rfqs(client):
    manager = _user("manager", "ai-sales-manager-scope@example.com")
    owner = _user("sales", "ai-sales-manager-owner@example.com")
    customer = BusinessCustomer.objects.create(
        company_name="Manager Scope Customer", contact_name="Buyer"
    )
    rfq = SalesRfq.objects.create(
        rfq_number="RFQ-MANAGER-SCOPE",
        customer=customer,
        quote_due_at=date(2026, 11, 1),
        required_delivery_date=date(2026, 12, 1),
        created_by=owner,
    )

    response = client.get(
        "/api/v1/internal/ai-sales/rfqs/", **_headers(manager)
    )
    assert response.status_code == 200
    assert rfq.id in {item["id"] for item in response.json()["data"]["results"]}


@override_settings(AI_SALES_KNOWLEDGE_SOURCE="production")
def test_ai_sales_production_knowledge_source_fails_closed():
    with pytest.raises(ImproperlyConfigured, match="production knowledge is not enabled"):
        AISalesKnowledgeSourceService().build()


def test_ai_sales_metrics_use_only_bounded_content_free_labels():
    class CapturingRegistry:
        def __init__(self):
            self.calls = []

        def increment(self, name, amount=1, **labels):
            self.calls.append((name, amount, labels))

    registry = CapturingRegistry()
    result = {
        "status": "SUPPORTED",
        "priority": "HIGH",
        "customer_display": "PRIVATE CUSTOMER NAME",
        "summary": "PRIVATE RFQ NOTES",
        "_telemetry": {
            "retrieval": "hit",
            "provider": "success",
            "deterministic_fallback": False,
        },
    }
    bounded = AISalesMetricsService(registry=registry).record(
        result, duration_seconds=0.125
    )

    rendered = str(registry.calls)
    assert "PRIVATE CUSTOMER NAME" not in rendered
    assert "PRIVATE RFQ NOTES" not in rendered
    assert bounded == {
        "status": "SUPPORTED",
        "priority": "HIGH",
        "retrieval": "hit",
        "provider": "success",
        "deterministic_fallback": False,
    }
    assert "mecprecision_ai_sales_requests_total" in rendered
    assert "mecprecision_ai_sales_response_seconds_sum" in rendered


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
