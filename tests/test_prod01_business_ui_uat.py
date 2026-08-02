"""End-to-end HTTP validation for PROD-01 Business UI workflows."""

from pathlib import Path

import pytest
from apps.business_core.models import BusinessCustomer, BusinessProduct
from apps.crm.models import CrmInteraction, CrmNote, CrmTask, CrmTimelineEvent
from apps.foundation.models import FoundationPermission, FoundationRole
from apps.foundation.services import FoundationAuthService, FoundationUserService
from apps.sales.models import (
    SalesActivity,
    SalesFollowUp,
    SalesLead,
    SalesOpportunity,
    SalesQuotation,
)
from django.test import Client

PASSWORD = "Prod01SecurePass123!"
SESSION_KEY = "foundation_admin_token"


def create_role(name, permission_codes):
    """Create a test role with an explicit module permission matrix."""
    role = FoundationRole.objects.create(name=name, description=f"PROD-01 {name}")
    for code in permission_codes:
        module, action = code.split(":", 1)
        permission, _created = FoundationPermission.objects.get_or_create(
            code=code,
            defaults={"module": module, "action": action, "description": code},
        )
        role.permissions.add(permission)
    return role


def create_user(email, role):
    """Create one Foundation user for a role-specific browser session."""
    return FoundationUserService().create_user(
        email=email,
        full_name=email.split("@", 1)[0].replace(".", " ").title(),
        password=PASSWORD,
        role_name=role.name,
    )


def login_session(client, user):
    """Attach a real Foundation token to the shared Business UI session."""
    raw_token, _token = FoundationAuthService().login(user.email, PASSWORD)
    session = client.session
    session[SESSION_KEY] = raw_token
    session.save()


@pytest.mark.django_db
def test_module_permissions_match_ceo_sales_crm_technical_and_admin_roles(client):
    """Each operational role sees only the modules assigned to it."""
    role_matrix = {
        "prod01-ceo": [
            "dashboard:read",
            "sales:read",
            "crm:read",
            "ai_sales:read",
            "knowledge:read",
        ],
        "prod01-sales-manager": [
            "dashboard:read",
            "sales:read",
            "sales:write",
            "sales:approve",
            "crm:read",
        ],
        "prod01-sales": [
            "dashboard:read",
            "sales:read",
            "sales:write",
            "crm:read",
            "ai_sales:read",
            "ai_sales:write",
        ],
        "prod01-crm": ["dashboard:read", "crm:read", "crm:write"],
        "prod01-technical": ["dashboard:read", "knowledge:read", "knowledge:write"],
        "prod01-admin": [
            "dashboard:read",
            "sales:read",
            "sales:write",
            "sales:approve",
            "crm:read",
            "crm:write",
            "ai_sales:read",
            "ai_sales:write",
            "knowledge:read",
            "knowledge:write",
        ],
    }
    users = {}
    for role_name, permission_codes in role_matrix.items():
        users[role_name] = create_user(
            f"{role_name}@example.com", create_role(role_name, permission_codes)
        )

    expected_pages = {
        "prod01-ceo": [
            "/business/",
            "/business/leads/",
            "/business/customers/",
            "/business/ai-sales/",
            "/business/documents/",
        ],
        "prod01-sales-manager": [
            "/business/",
            "/business/leads/",
            "/business/customers/",
            "/business/quotations/",
        ],
        "prod01-sales": [
            "/business/",
            "/business/leads/",
            "/business/customers/",
            "/business/ai-sales/",
        ],
        "prod01-crm": ["/business/", "/business/customers/"],
        "prod01-technical": ["/business/", "/business/documents/"],
        "prod01-admin": [
            "/business/",
            "/business/leads/",
            "/business/customers/",
            "/business/quotations/",
            "/business/ai-sales/",
            "/business/documents/",
        ],
    }
    for role_name, pages in expected_pages.items():
        role_client = Client()
        login_session(role_client, users[role_name])
        for page in pages:
            assert role_client.get(page).status_code == 200

    crm_client = Client()
    login_session(crm_client, users["prod01-crm"])
    assert crm_client.get("/business/leads/").status_code == 403
    technical_client = Client()
    login_session(technical_client, users["prod01-technical"])
    assert technical_client.get("/business/customers/").status_code == 403


@pytest.mark.django_db
def test_sales_crm_quotation_approval_and_handoff_workflow(client):
    """Run lead, CRM, quotation approval, follow-up, and handoff through UI actions."""
    admin_role = FoundationRole.objects.get(name="admin")
    admin = create_user("prod01-admin-workflow@example.com", admin_role)
    assignee = create_user("prod01-assignee@example.com", admin_role)
    login_session(client, admin)
    customer = BusinessCustomer.objects.create(
        company_name="PROD-01 CNC Customer",
        contact_name="Buyer",
        email="buyer@example.com",
    )
    product = BusinessProduct.objects.create(
        name="PROD-01 CNC Shaft",
        slug="prod01-cnc-shaft",
        status="published",
    )

    assert (
        client.post(
            "/business/leads/create/",
            {
                "company": customer.company_name,
                "contact_person": customer.contact_name,
                "priority": "high",
            },
        ).status_code
        == 302
    )
    lead = SalesLead.objects.get(company=customer.company_name)
    assert (
        client.post(
            f"/business/leads/{lead.id}/assign/", {"owner_id": assignee.id}
        ).status_code
        == 302
    )
    assert (
        client.post(
            f"/business/leads/{lead.id}/transition/", {"status": "contacted"}
        ).status_code
        == 302
    )
    assert (
        client.post(
            f"/business/leads/{lead.id}/opportunities/create/",
            {
                "customer_id": customer.id,
                "title": "Annual shaft supply",
                "value": "5000",
                "probability": "70",
            },
        ).status_code
        == 302
    )
    assert (
        client.post(
            f"/business/leads/{lead.id}/follow-ups/create/",
            {"title": "Confirm drawing", "due_date": "2026-08-10"},
        ).status_code
        == 302
    )

    opportunity = SalesOpportunity.objects.get(lead=lead)
    assert (
        client.post(
            "/business/quotations/create/",
            {
                "opportunity_id": opportunity.id,
                "customer_id": customer.id,
                "product_id": product.id,
                "description": "Precision shaft batch",
                "quantity": "10",
                "unit_price": "125",
                "discount": "50",
            },
        ).status_code
        == 302
    )
    quotation = SalesQuotation.objects.get(opportunity=opportunity)
    assert quotation.total == 1200
    assert (
        client.post(f"/business/quotations/{quotation.id}/approve/").status_code == 302
    )
    quotation.refresh_from_db()
    assert quotation.approval_status == "approved"
    assert (
        client.post(f"/business/quotations/{quotation.id}/handoff/").status_code == 302
    )
    quotation.refresh_from_db()
    assert quotation.status == "accepted"

    detail_url = f"/business/customers/{customer.id}/"
    assert (
        client.post(
            f"{detail_url}interactions/create/",
            {
                "interaction_type": "call",
                "subject": "Drawing review",
                "content": "Tolerance confirmed",
            },
        ).status_code
        == 302
    )
    assert (
        client.post(
            f"{detail_url}notes/create/", {"note": "Customer prefers weekly updates"}
        ).status_code
        == 302
    )
    assert (
        client.post(
            f"{detail_url}tasks/create/",
            {
                "title": "Send revised quotation",
                "due_date": "2026-08-11",
                "owner_id": assignee.id,
            },
        ).status_code
        == 302
    )

    assert SalesFollowUp.objects.filter(lead=lead, owner=admin).exists()
    assert SalesActivity.objects.filter(lead=lead, activity_type="assignment").exists()
    assert SalesActivity.objects.filter(activity_type="quotation_approval").exists()
    assert SalesActivity.objects.filter(activity_type="order_handoff").exists()
    assert CrmInteraction.objects.filter(customer=customer).exists()
    assert CrmNote.objects.filter(customer=customer).exists()
    assert CrmTask.objects.filter(customer=customer, owner=assignee).exists()
    assert CrmTimelineEvent.objects.filter(customer=customer).count() == 3


@pytest.mark.django_db
def test_quotation_approval_requires_dedicated_permission(client):
    """Sales write access cannot substitute for human approval permission."""
    sales_role = create_role("prod01-sales-no-approve", ["sales:read", "sales:write"])
    sales_user = create_user("prod01-no-approve@example.com", sales_role)
    quotation = SalesQuotation.objects.create(
        quotation_number="PROD01-NO-APPROVE", status="review"
    )
    login_session(client, sales_user)

    response = client.post(f"/business/quotations/{quotation.id}/approve/")

    assert response.status_code == 403
    quotation.refresh_from_db()
    assert quotation.approval_status == "pending"


@pytest.mark.django_db
def test_business_write_actions_require_csrf():
    """A valid business session cannot bypass CSRF on browser writes."""
    admin = create_user(
        "prod01-csrf@example.com", FoundationRole.objects.get(name="admin")
    )
    csrf_client = Client(enforce_csrf_checks=True)
    login_session(csrf_client, admin)

    response = csrf_client.post(
        "/business/leads/create/",
        {"company": "CSRF Co", "contact_person": "Blocked"},
    )

    assert response.status_code == 403
    assert not SalesLead.objects.filter(company="CSRF Co").exists()


@pytest.mark.django_db
def test_business_forms_reject_invalid_server_side_values(client):
    """Required fields and monetary limits remain enforced without browser HTML."""
    sales_role = create_role("prod01-validation-sales", ["sales:read", "sales:write"])
    sales_user = create_user("prod01-validation-sales@example.com", sales_role)
    lead = SalesLead.objects.create(company="Validation", contact_person="Buyer")
    login_session(client, sales_user)

    assert (
        client.post(
            f"/business/leads/{lead.id}/opportunities/create/",
            {"title": "", "value": "100", "probability": "10"},
        ).status_code
        == 400
    )
    assert (
        client.post(
            f"/business/leads/{lead.id}/follow-ups/create/", {"title": ""}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/business/quotations/create/",
            {
                "description": "Invalid discount",
                "quantity": "1",
                "unit_price": "100",
                "discount": "101",
            },
        ).status_code
        == 400
    )

    crm_role = create_role("prod01-validation-crm", ["crm:read", "crm:write"])
    crm_user = create_user("prod01-validation-crm@example.com", crm_role)
    customer = BusinessCustomer.objects.create(
        company_name="Validation Customer", contact_name="Contact"
    )
    login_session(client, crm_user)
    assert (
        client.post(
            f"/business/customers/{customer.id}/interactions/create/",
            {"subject": ""},
        ).status_code
        == 400
    )
    assert (
        client.post(
            f"/business/customers/{customer.id}/tasks/create/", {"title": ""}
        ).status_code
        == 400
    )


def test_ai_business_templates_render_structured_cards_not_raw_dictionaries():
    """AI Sales and Document pages must address structured fields explicitly."""
    root = Path("django_backend/apps/business_ui/templates/business_ui")
    sales_template = (root / "ai_sales.html").read_text(encoding="utf-8")
    document_template = (root / "documents.html").read_text(encoding="utf-8")

    assert "{{ result }}" not in sales_template
    assert "{{ result }}" not in document_template
    assert "{{ answer }}" not in document_template
    assert "{{ document.metadata }}" not in document_template
    assert "result.synthesis.summary" in sales_template
    assert "result.classification" in document_template
    assert "answer.sources" in document_template
