import pytest
from django.core.management import call_command

from apps.business_core.models import BusinessCustomer, BusinessProduct
from apps.crm.models import CrmCustomerProfile, CrmInteraction, CrmTask
from apps.foundation.models import FoundationRole, FoundationUser
from apps.knowledge.models import KnowledgeDocument
from apps.knowledge.services.search_service import KnowledgeSearchService
from apps.sales.models import SalesLead, SalesOpportunity, SalesQuotation
from apps.transaction_domain.models import TransactionOrder


DEMO_DOMAIN = "demo.mecprecision.local"


def generate_small_demo():
    """Generate a compact dataset so tests stay fast."""
    call_command(
        "generate_demo_data",
        customers=4,
        products=3,
        leads=5,
        activities=7,
        opportunities=3,
        quotations=3,
        orders=2,
        documents=2,
        seed=2026,
    )


@pytest.mark.django_db
def test_generate_demo_data_creates_master_and_transaction_data():
    generate_small_demo()

    assert FoundationUser.objects.filter(email__endswith=f"@{DEMO_DOMAIN}").count() == 7
    assert FoundationRole.objects.filter(name__startswith="demo-").count() >= 5
    assert BusinessCustomer.objects.filter(notes__contains="demo_data=true").count() == 4
    assert BusinessProduct.objects.filter(sku__startswith="DEMO-").count() == 3
    assert SalesLead.objects.filter(email__endswith=f"@{DEMO_DOMAIN}").count() == 5
    assert SalesOpportunity.objects.filter(title__startswith="[DEMO]").count() == 3
    assert SalesQuotation.objects.filter(quotation_number__startswith="SQ-DEMO-").count() == 3
    assert TransactionOrder.objects.filter(order_number__startswith="DO-DEMO-").count() == 2


@pytest.mark.django_db
def test_demo_data_relationship_integrity():
    generate_small_demo()

    quote = SalesQuotation.objects.filter(quotation_number__startswith="SQ-DEMO-").prefetch_related("lines").first()
    order = TransactionOrder.objects.filter(order_number__startswith="DO-DEMO-").prefetch_related("items").first()
    customer = BusinessCustomer.objects.filter(notes__contains="demo_data=true").first()

    assert quote.customer is not None
    assert quote.lines.count() >= 1
    assert quote.total > 0
    assert order.customer is not None
    assert order.items.count() >= 1
    assert CrmCustomerProfile.objects.filter(customer=customer).exists()
    assert CrmInteraction.objects.filter(customer=customer, subject__startswith="[DEMO]").exists()
    assert CrmTask.objects.filter(customer=customer, title__startswith="[DEMO]").exists()


@pytest.mark.django_db
def test_demo_permissions_are_assigned_to_users():
    generate_small_demo()

    sales_manager = FoundationUser.objects.select_related("role").get(email=f"sales.manager@{DEMO_DOMAIN}")
    permission_codes = set(sales_manager.role.permissions.values_list("code", flat=True))

    assert "sales:write" in permission_codes
    assert "crm:write" in permission_codes
    assert "ai_sales:read" in permission_codes


@pytest.mark.django_db
def test_clear_demo_data_removes_only_demo_records():
    manual_customer = BusinessCustomer.objects.create(
        company_name="Manual Customer",
        contact_name="Manual Contact",
        email="manual@example.com",
        notes="not demo",
    )
    generate_small_demo()

    call_command("clear_demo_data")

    assert BusinessCustomer.objects.filter(id=manual_customer.id).exists()
    assert BusinessCustomer.objects.filter(notes__contains="demo_data=true").count() == 0
    assert SalesLead.objects.filter(email__endswith=f"@{DEMO_DOMAIN}").count() == 0
    assert KnowledgeDocument.objects.filter(title__startswith="[DEMO]").count() == 0


@pytest.mark.django_db
def test_demo_knowledge_is_ai_search_compatible():
    generate_small_demo()
    user = FoundationUser.objects.get(email=f"engineer1@{DEMO_DOMAIN}")

    result = KnowledgeSearchService().search("CNC material quality inspection", user=user)

    assert result["sources"]
    assert result["confidence"] > 0
    assert result["sources"][0]["title"].startswith("[DEMO]")
