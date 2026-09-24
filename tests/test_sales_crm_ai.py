import pytest

from apps.business_core.models import BusinessCustomer, BusinessProduct
from apps.crm.models import CrmCustomerProfile, CrmInteraction, CrmTimelineEvent
from apps.foundation.services import FoundationAuthService, FoundationUserService
from apps.knowledge.services.knowledge_service import KnowledgeService
from tests.knowledge_test_helpers import create_approved_indexed_knowledge
from apps.sales.models import SalesActivity, SalesLead, SalesOpportunity, SalesQuotation


@pytest.fixture
def sales_admin():
    """Create a Django user that can manage sales, CRM, and AI sales features."""
    return FoundationUserService().create_user(
        email="sales-admin@example.com",
        full_name="Sales Admin",
        password="SecurePass123!",
        role_name="admin",
    )


@pytest.fixture
def viewer_user():
    """Create a read-only user for permission tests."""
    return FoundationUserService().create_user(
        email="sales-viewer@example.com",
        full_name="Sales Viewer",
        password="SecurePass123!",
        role_name="viewer",
    )


def bearer_header(user):
    """Create an HTTP Authorization header for Django test client requests."""
    token, _token_row = FoundationAuthService().login(user.email, "SecurePass123!")
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.mark.django_db
def test_sales_lead_creation_requires_permission(client, sales_admin, viewer_user):
    payload = {
        "company": "ABC Precision",
        "contact_person": "Nguyen Van A",
        "email": "a@example.com",
        "industry": "CNC machining",
        "priority": "high",
        "notes": "Customer needs CNC shaft quotation.",
    }

    missing_token_response = client.post(
        "/api/v1/sales/leads/",
        data=payload,
        content_type="application/json",
    )
    viewer_response = client.post(
        "/api/v1/sales/leads/",
        data=payload,
        content_type="application/json",
        **bearer_header(viewer_user),
    )
    admin_response = client.post(
        "/api/v1/sales/leads/",
        data=payload,
        content_type="application/json",
        **bearer_header(sales_admin),
    )

    assert missing_token_response.status_code == 403
    assert viewer_response.status_code == 403
    assert admin_response.status_code == 201
    assert admin_response.json()["data"]["company"] == "ABC Precision"
    assert SalesLead.objects.filter(company="ABC Precision", owner=sales_admin).exists()


@pytest.mark.django_db
def test_sales_pipeline_opportunity_quotation_and_dashboard(client, sales_admin):
    lead = SalesLead.objects.create(
        company="Pipeline Customer",
        contact_person="Tran B",
        industry="fixture",
        priority="high",
        owner=sales_admin,
    )
    customer = BusinessCustomer.objects.create(
        company_name="Pipeline Customer",
        contact_name="Tran B",
        email="pipeline@example.com",
    )
    product = BusinessProduct.objects.create(
        name="Precision Shaft",
        slug="precision-shaft-test",
        sku="SHAFT-001",
        price="125.00",
        status="published",
    )
    headers = bearer_header(sales_admin)

    transition_response = client.post(
        f"/api/v1/sales/leads/{lead.id}/transition/",
        data={"status": "contacted"},
        content_type="application/json",
        **headers,
    )
    opportunity_response = client.post(
        "/api/v1/sales/opportunities/",
        data={
            "lead_id": lead.id,
            "customer_id": customer.id,
            "title": "CNC shaft annual supply",
            "value": "5000.00",
            "probability": 70,
            "status": "proposal",
        },
        content_type="application/json",
        **headers,
    )
    opportunity_id = opportunity_response.json()["data"]["id"]
    quotation_response = client.post(
        "/api/v1/sales/quotations/",
        data={
            "opportunity_id": opportunity_id,
            "customer_id": customer.id,
            "lines": [
                {
                    "product_id": product.id,
                    "description": "Precision shaft batch",
                    "quantity": "10",
                    "unit_price": "125.00",
                    "discount": "50.00",
                }
            ],
        },
        content_type="application/json",
        **headers,
    )
    dashboard_response = client.get("/api/v1/sales/dashboard/", **headers)

    assert transition_response.status_code == 200
    lead.refresh_from_db()
    assert lead.status == "contacted"
    assert SalesActivity.objects.filter(lead=lead, activity_type="pipeline").exists()
    assert opportunity_response.status_code == 201
    assert SalesOpportunity.objects.filter(id=opportunity_id, value="5000.00").exists()
    assert quotation_response.status_code == 201
    assert quotation_response.json()["data"]["total"] == "1200.00"
    assert SalesQuotation.objects.filter(customer=customer, total="1200.00").exists()
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["data"]["lead_count"] >= 1


@pytest.mark.django_db
def test_crm_customer_profile_and_interaction_timeline(client, sales_admin):
    headers = bearer_header(sales_admin)
    create_response = client.post(
        "/api/v1/crm/customers/",
        data={
            "company_name": "CRM Demo Co",
            "contact_name": "Le Thi C",
            "email": "crm@example.com",
            "phone": "0900123456",
            "segment": "enterprise",
            "lifecycle_stage": "qualified",
            "summary": "Needs recurring CNC supplier.",
        },
        content_type="application/json",
        **headers,
    )
    customer_id = create_response.json()["data"]["id"]
    interaction_response = client.post(
        f"/api/v1/crm/customers/{customer_id}/interactions/",
        data={
            "interaction_type": "call",
            "subject": "Initial discovery call",
            "content": "Customer asked about fixture tolerance.",
        },
        content_type="application/json",
        **headers,
    )
    detail_response = client.get(f"/api/v1/crm/customers/{customer_id}/", **headers)

    assert create_response.status_code == 201
    assert CrmCustomerProfile.objects.filter(customer_id=customer_id, segment="enterprise").exists()
    assert interaction_response.status_code == 201
    assert CrmInteraction.objects.filter(customer_id=customer_id, subject="Initial discovery call").exists()
    assert CrmTimelineEvent.objects.filter(customer_id=customer_id, event_type="interaction").exists()
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["customer"]["company_name"] == "CRM Demo Co"


@pytest.mark.django_db
def test_ai_sales_assistant_uses_rag_and_keeps_human_approval(client, sales_admin):
    create_approved_indexed_knowledge(
        title="CNC shaft capability",
        content="MecPrecision supports CNC shaft machining, fixture design, and quality inspection.",
        category_name="Sales",
        permission_level="internal",
        reader=sales_admin,
    )
    lead = SalesLead.objects.create(
        company="AI Lead Co",
        contact_person="Pham D",
        industry="CNC",
        priority="high",
        notes="Needs precision shaft and fixture quotation.",
        owner=sales_admin,
    )
    customer = BusinessCustomer.objects.create(
        company_name="AI Lead Co",
        contact_name="Pham D",
        email="ai-lead@example.com",
    )
    headers = bearer_header(sales_admin)

    analysis_response = client.post(
        "/api/v1/ai/sales-assistant/",
        data={"action": "lead_analysis", "payload": {"lead_id": lead.id}},
        content_type="application/json",
        **headers,
    )
    email_response = client.post(
        "/api/v1/ai/sales-assistant/",
        data={
            "action": "email_draft",
            "payload": {"lead_id": lead.id, "customer_id": customer.id, "product_interest": "CNC shaft"},
        },
        content_type="application/json",
        **headers,
    )

    assert analysis_response.status_code == 200
    analysis = analysis_response.json()["data"]
    assert analysis["human_approval_required"] is True
    assert analysis["autonomous_action"] is False
    assert analysis["score"] >= 70
    assert analysis["knowledge"]["sources"]

    assert email_response.status_code == 200
    draft = email_response.json()["data"]
    assert draft["human_approval_required"] is True
    assert draft["delivery_status"] == "draft_only_not_sent"
    assert "CNC shaft" in draft["draft"]["subject"]
