"""Focused validation tests for demo data, browser UI, API, and AI grounding."""

from __future__ import annotations

import pytest
from apps.ai_agent.services.sales_assistant import SalesAssistantService
from apps.business_core.models import BusinessCustomer, BusinessProduct
from apps.business_core.services import BusinessCustomerService, BusinessProductService
from apps.core.demo_database_validation import collect_demo_database_validation
from apps.crm.models import CrmCustomerProfile
from apps.foundation.models import FoundationUser
from apps.foundation.services import FoundationUserService
from apps.knowledge.models import KnowledgeChunk, KnowledgeDocument, KnowledgeEmbedding
from apps.sales.models import SalesLead, SalesQuotation
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.fixture
def demo_admin():
    return FoundationUserService().create_user(
        email="demo-validation-admin@example.com",
        full_name="Demo Validation Admin",
        password="SecurePass123!",
        role_name="admin",
    )


@pytest.mark.django_db
def test_orm_and_sqlite_counts_match_for_seeded_validation_database():
    BusinessProduct.objects.create(
        name="Demo Product", slug="demo-product", category_name="CNC"
    )
    customer = BusinessCustomer.objects.create(
        contact_name="Demo Customer", company_name="Demo Co"
    )
    CrmCustomerProfile.objects.create(customer=customer)
    SalesLead.objects.create(
        company="Demo Co", contact_person="Buyer", lead_source="website"
    )
    SalesQuotation.objects.create(customer=customer, quotation_number="DEMO-VAL-001")
    document = KnowledgeDocument.objects.create(
        title="Demo Knowledge", content="CNC machining"
    )
    chunk = KnowledgeChunk.objects.create(
        document=document, content="CNC machining", chunk_index=0
    )
    KnowledgeEmbedding.objects.create(chunk=chunk, vector=[0.1, 0.2], dimension=2)

    expected = {
        "products": BusinessProduct.objects.count(),
        "customers": CrmCustomerProfile.objects.count(),
        "leads": SalesLead.objects.count(),
        "quotations": SalesQuotation.objects.count(),
        "knowledge_documents": KnowledgeDocument.objects.count(),
        "users": FoundationUser.objects.count(),
    }
    result = collect_demo_database_validation(expected)

    assert result["orm_sqlite_consistent"] is True
    assert set(result["count_status"].values()) == {"PASS"}
    assert result["read_only_validation"] is True


@pytest.mark.django_db
def test_integrity_validation_detects_blocking_invalid_product_data():
    BusinessProduct.objects.create(name="Invalid Price", slug="invalid-price", price=-1)

    result = collect_demo_database_validation(
        {
            "products": 1,
            "customers": 0,
            "leads": 0,
            "quotations": 0,
            "knowledge_documents": 0,
            "users": 0,
        }
    )

    codes = {item["code"] for item in result["integrity_findings"]["high"]}
    assert "products_negative_price" in codes
    assert result["decision"] == "DEMO_DATABASE_VALIDATION_FAILED"


@pytest.mark.django_db
def test_crud_isolated_by_django_test_database_and_services():
    product = BusinessProductService().create_product(
        name="CRUD Product", slug="crud-product", price="10"
    )
    customer = BusinessCustomerService().create_customer(
        contact_name="CRUD Customer", company_name="CRUD Co"
    )
    BusinessProductService().update_product(product, name="CRUD Product Updated")
    BusinessCustomerService().update_customer(customer, status="inactive")

    assert BusinessProduct.objects.get(pk=product.pk).name == "CRUD Product Updated"
    assert BusinessCustomer.objects.get(pk=customer.pk).status == "inactive"

    product.delete()
    customer.delete()
    assert not BusinessProduct.objects.filter(pk=product.pk).exists()
    assert not BusinessCustomer.objects.filter(pk=customer.pk).exists()


@pytest.mark.django_db
def test_admin_login_and_ui_render_database_values(client, demo_admin):
    BusinessProduct.objects.create(
        name="UI Database Product", slug="ui-database-product"
    )
    response = client.post(
        "/admin/login/",
        {"email": demo_admin.email, "password": "SecurePass123!"},
        follow=True,
    )
    products = client.get("/admin/products/")

    assert response.status_code == 200
    assert client.session.get("foundation_admin_token")
    assert products.status_code == 200
    assert b"UI Database Product" in products.content


@pytest.mark.django_db
def test_business_api_reads_database_product(client, demo_admin):
    product = BusinessProduct.objects.create(
        name="API Database Product", slug="api-database-product"
    )
    login = client.post(
        "/api/v1/foundation/auth/login/",
        data={"email": demo_admin.email, "password": "SecurePass123!"},
        content_type="application/json",
    )
    assert login.status_code == 200
    token = login.json()["data"]["token"]

    response = client.get(
        "/api/v1/business/products/", HTTP_AUTHORIZATION=f"Bearer {token}"
    )
    assert response.status_code == 200
    assert str(product.id).encode() in response.content
    assert b"API Database Product" in response.content


@pytest.mark.django_db
def test_ai_sales_context_is_grounded_in_database_and_requires_human_approval(
    demo_admin,
):
    lead = SalesLead.objects.create(
        company="AI Grounded Customer",
        contact_person="Buyer",
        lead_source="website",
        notes="Needs precision CNC shaft quotation",
        owner=demo_admin,
    )
    result = SalesAssistantService().handle(
        "lead_analysis", {"lead_id": lead.id}, user=demo_admin
    )

    assert result["human_approval_required"] is True
    assert result["autonomous_action"] is False
    assert "AI Grounded Customer" in str(result)


@pytest.mark.django_db
def test_management_command_can_write_json_report(tmp_path):
    output = tmp_path / "validation.json"
    call_command("validate_demo_database", json_output=output)
    assert output.exists()
    assert '"read_only_validation": true' in output.read_text(encoding="utf-8")


@pytest.mark.django_db
def test_management_command_fails_closed_for_high_findings(tmp_path):
    BusinessProduct.objects.create(
        name="Invalid Price", slug="command-invalid-price", price=-1
    )
    output = tmp_path / "failed-validation.json"

    with pytest.raises(CommandError, match="blocking issues"):
        call_command("validate_demo_database", json_output=output)

    assert '"decision": "DEMO_DATABASE_VALIDATION_FAILED"' in output.read_text(
        encoding="utf-8"
    )
