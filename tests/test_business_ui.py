from decimal import Decimal

import pytest

from apps.business_core.models import BusinessCustomer, BusinessProduct
from apps.crm.models import CrmInteraction, CrmNote, CrmTask, CrmTimelineEvent
from apps.foundation.models import FoundationUser
from apps.foundation.services import FoundationUserService
from apps.sales.models import SalesLead, SalesOpportunity, SalesQuotation, SalesQuotationLine


@pytest.fixture
def business_admin():
    """Tao user admin dung de dang nhap giao dien business."""
    existing = FoundationUser.objects.filter(email="business-ui-admin@example.com").first()
    if existing:
        return existing
    return FoundationUserService().create_user(
        email="business-ui-admin@example.com",
        full_name="Business UI Admin",
        password="SecurePass123!",
        role_name="admin",
    )


def login(client, user):
    """Dang nhap qua CMS admin vi Business UI dung chung session token."""
    return client.post(
        "/admin/login/",
        data={"email": user.email, "password": "SecurePass123!"},
        follow=True,
    )


@pytest.mark.django_db
def test_business_dashboard_requires_login(client):
    response = client.get("/business/")

    assert response.status_code == 302
    assert response["Location"].endswith("/admin/login/")


@pytest.mark.django_db
def test_business_dashboard_renders_sales_metrics(client, business_admin):
    login(client, business_admin)
    SalesLead.objects.create(company="Demo CNC", contact_person="Quan", status="won", priority="high")
    SalesOpportunity.objects.create(title="Fixture order", value=Decimal("1000"), probability=50, status="open")

    response = client.get("/business/")

    assert response.status_code == 200
    assert b"Sales Dashboard" in response.content
    assert b"Pipeline value" in response.content


@pytest.mark.django_db
def test_lead_pipeline_and_ai_sales_pages_render(client, business_admin):
    login(client, business_admin)
    lead = SalesLead.objects.create(
        company="Precision Buyer",
        contact_person="Ms Linh",
        industry="CNC fixture",
        status="meeting",
        priority="high",
        notes="Need CNC fixture quotation",
    )

    pipeline_response = client.get("/business/leads/")
    ai_response = client.post(
        "/business/ai-sales/",
        data={"action": "lead_analysis", "lead_id": str(lead.id)},
        follow=True,
    )

    assert pipeline_response.status_code == 200
    assert b"Precision Buyer" in pipeline_response.content
    assert ai_response.status_code == 200
    assert b"human_approval_required" in ai_response.content


@pytest.mark.django_db
def test_crm_customer_detail_renders_timeline_notes_tasks(client, business_admin):
    login(client, business_admin)
    customer = BusinessCustomer.objects.create(company_name="MEC Client", contact_name="Mr Nam", email="nam@example.com")
    CrmInteraction.objects.create(customer=customer, subject="Intro call", content="Discussed CNC shaft")
    CrmNote.objects.create(customer=customer, note="Need follow up")
    CrmTask.objects.create(customer=customer, title="Send catalogue")
    CrmTimelineEvent.objects.create(customer=customer, event_type="note", title="CRM note added")

    response = client.get(f"/business/customers/{customer.id}/")

    assert response.status_code == 200
    assert b"MEC Client" in response.content
    assert b"Intro call" in response.content
    assert b"Send catalogue" in response.content


@pytest.mark.django_db
def test_quotation_list_and_detail_render(client, business_admin):
    login(client, business_admin)
    customer = BusinessCustomer.objects.create(company_name="Quote Client", contact_name="Buyer")
    product = BusinessProduct.objects.create(name="CNC Shaft", slug="business-ui-cnc-shaft")
    quotation = SalesQuotation.objects.create(
        customer=customer,
        quotation_number="BQ-UI-001",
        status="review",
        approval_status="pending",
        total=Decimal("2500"),
        created_by=business_admin,
    )
    SalesQuotationLine.objects.create(
        quotation=quotation,
        product=product,
        description="Precision CNC shaft",
        quantity=2,
        unit_price=Decimal("1250"),
        line_total=Decimal("2500"),
    )

    list_response = client.get("/business/quotations/")
    detail_response = client.get(f"/business/quotations/{quotation.id}/")

    assert list_response.status_code == 200
    assert b"BQ-UI-001" in list_response.content
    assert detail_response.status_code == 200
    assert b"Precision CNC shaft" in detail_response.content

