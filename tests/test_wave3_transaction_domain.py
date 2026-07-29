import sqlite3

import pytest

from apps.business_core.models import (
    BusinessCustomer,
    BusinessProduct,
    InventoryItem,
    InventoryWarehouse,
)
from apps.business_core.services import InventoryService
from apps.foundation.models import FoundationUser
from apps.foundation.services import FoundationAuthService, FoundationUserService
from apps.sales.models import QuoteRequest
from apps.sales.repositories.quotation_repository import QuotationRepository
from apps.transaction_domain.models import (
    OrderStatusHistory,
    TransactionHistory,
    TransactionOrder,
    WorkflowApproval,
)
from apps.transaction_domain.services import OrderService, WorkflowService
from scripts.copy_legacy_database_for_test import copy_legacy_database


@pytest.fixture
def legacy_db(tmp_path):
    """Return a read-only copied legacy database path."""
    return copy_legacy_database(
        destination=tmp_path / "legacy_database" / "mecprecision-test.sqlite"
    )


def count_legacy_rows(legacy_db, table_name):
    """Count rows in a copied legacy table without writing to it."""
    connection_uri = f"file:{legacy_db.as_posix()}?mode=ro"
    with sqlite3.connect(connection_uri, uri=True) as legacy_connection:
        return legacy_connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


@pytest.fixture
def foundation_admin():
    """Create or reuse one Django-owned admin user for protected API calls."""
    existing = FoundationUser.objects.filter(email="wave3-admin@example.com").first()
    if existing:
        return existing
    return FoundationUserService().create_user(
        email="wave3-admin@example.com",
        full_name="Wave 3 Admin",
        password="SecurePass123!",
        role_name="admin",
    )


def bearer_header(user):
    """Create one Bearer token header."""
    token, _token_row = FoundationAuthService().login(user.email, "SecurePass123!")
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def create_stock_item(quantity="20"):
    """Create a product, warehouse, and stock item for order tests."""
    product = BusinessProduct.objects.create(
        name="Wave 3 Product",
        slug=f"wave-3-product-{BusinessProduct.objects.count() + 1}",
        sku="W3",
        price="15.00",
        status="published",
    )
    warehouse = InventoryWarehouse.objects.create(
        code=f"W3{InventoryWarehouse.objects.count() + 1}",
        name="Wave 3 Warehouse",
    )
    item = InventoryService().create_item(product=product, warehouse=warehouse, quantity=quantity)
    return product, item


@pytest.mark.django_db
def test_wave3_migrations_seed_orders_and_transaction_history():
    assert TransactionOrder.objects.filter(legacy_quote_request_id__isnull=False).count() >= 1
    assert TransactionHistory.objects.filter(action="order.imported").count() >= 1
    assert TransactionHistory.objects.filter(legacy_event_id__isnull=False).count() >= 1


@pytest.mark.django_db
def test_order_service_creates_order_with_customer_inventory_and_history():
    customer = BusinessCustomer.objects.create(contact_name="Wave 3 Customer", email="wave3@example.com")
    product, inventory_item = create_stock_item(quantity="20")

    order = OrderService().create_order(
        customer_id=customer.id,
        project_name="Precision fixture order",
        message="Need machining service",
        actor="wave3-admin@example.com",
        items=[
            {
                "product_id": product.id,
                "inventory_item_id": inventory_item.id,
                "quantity": 3,
                "unit_price": "15.00",
                "drawing_code": "DRW-001",
            }
        ],
    )

    inventory_item.refresh_from_db()
    assert order.id
    assert order.order_number.startswith("ORD-")
    assert order.customer_id == customer.id
    assert order.items.count() == 1
    assert order.total_amount == 45
    assert inventory_item.quantity == 17
    assert OrderStatusHistory.objects.filter(order=order, to_status="new").exists()
    assert TransactionHistory.objects.filter(order=order, action="order.created").exists()


@pytest.mark.django_db
def test_order_service_rolls_back_when_inventory_would_be_negative():
    customer = BusinessCustomer.objects.create(contact_name="Rollback Customer")
    product, inventory_item = create_stock_item(quantity="1")

    with pytest.raises(Exception):
        OrderService().create_order(
            customer_id=customer.id,
            project_name="Impossible order",
            actor="wave3-admin@example.com",
            items=[
                {
                    "product_id": product.id,
                    "inventory_item_id": inventory_item.id,
                    "quantity": 2,
                    "unit_price": "10.00",
                }
            ],
        )

    inventory_item.refresh_from_db()
    assert inventory_item.quantity == 1
    assert TransactionOrder.objects.filter(project_name="Impossible order").exists() is False


@pytest.mark.django_db
def test_workflow_service_transitions_order_and_creates_approval():
    customer = BusinessCustomer.objects.create(contact_name="Workflow Customer")
    order = OrderService().create_order(customer_id=customer.id, project_name="Workflow order")

    transitioned = WorkflowService().transition_order(
        order=order,
        target_status="approved",
        actor="wave3-admin@example.com",
        note="Approved for processing",
    )

    assert transitioned.status == "approved"
    assert WorkflowApproval.objects.filter(order=order, decision="approved").exists()
    assert OrderStatusHistory.objects.filter(order=order, from_status="new", to_status="approved").exists()
    assert TransactionHistory.objects.filter(order=order, action="workflow.transition").exists()


@pytest.mark.django_db
def test_order_api_create_update_and_detail(client, foundation_admin):
    headers = bearer_header(foundation_admin)
    customer = BusinessCustomer.objects.create(contact_name="API Order Customer")
    product, inventory_item = create_stock_item(quantity="12")

    create_response = client.post(
        "/api/v1/orders/",
        data={
            "customer_id": customer.id,
            "project_name": "API order",
            "message": "Created from API",
            "items": [
                {
                    "product_id": product.id,
                    "inventory_item_id": inventory_item.id,
                    "quantity": 2,
                    "unit_price": "18.50",
                }
            ],
        },
        content_type="application/json",
        **headers,
    )
    order_id = create_response.json()["data"]["id"]
    update_response = client.put(
        f"/api/v1/orders/{order_id}/",
        data={"internal_note": "Reviewed by sales"},
        content_type="application/json",
        **headers,
    )
    detail_response = client.get(f"/api/v1/orders/{order_id}/", **headers)

    assert create_response.status_code == 201
    assert update_response.status_code == 200
    assert update_response.json()["data"]["internal_note"] == "Reviewed by sales"
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["items"][0]["quantity"] == 2


@pytest.mark.django_db
def test_workflow_api_requires_permission_and_transitions_order(client, foundation_admin):
    headers = bearer_header(foundation_admin)
    customer = BusinessCustomer.objects.create(contact_name="Workflow API Customer")
    order = OrderService().create_order(customer_id=customer.id, project_name="API workflow")

    response = client.post(
        "/api/v1/workflows/",
        data={"order_id": order.id, "target_status": "approved", "note": "Approved by API"},
        content_type="application/json",
        **headers,
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "approved"


@pytest.mark.django_db
def test_transaction_history_api_lists_history(client, foundation_admin):
    headers = bearer_header(foundation_admin)
    customer = BusinessCustomer.objects.create(contact_name="History API Customer")
    order = OrderService().create_order(customer_id=customer.id, project_name="History order")

    response = client.get("/api/v1/transactions/", **headers)

    assert response.status_code == 200
    actions = [row["action"] for row in response.json()["data"]["results"]]
    assert "order.created" in actions
    assert TransactionHistory.objects.filter(order=order).exists()


@pytest.mark.django_db
def test_order_api_requires_authentication(client):
    response = client.get("/api/v1/orders/")

    assert response.status_code == 403
    assert response.json()["success"] is False


@pytest.mark.django_db
def test_workflow_service_rejects_invalid_transition():
    customer = BusinessCustomer.objects.create(contact_name="Invalid Workflow Customer")
    order = OrderService().create_order(customer_id=customer.id, project_name="Invalid workflow")

    with pytest.raises(Exception):
        WorkflowService().transition_order(order=order, target_status="completed")

    order.refresh_from_db()
    assert order.status == "new"


@pytest.mark.django_db
def test_legacy_quote_compatibility_remains_read_only(legacy_db):
    assert QuoteRequest._meta.managed is False
    assert QuotationRepository().list_quotes()._db == "legacy"
    assert count_legacy_rows(legacy_db, "quote_requests") >= 1

    legacy_quote = QuoteRequest(
        id=999,
        customer_id=1,
        project_name="Legacy quote",
        status="new",
        created_at="2026-01-01 00:00:00",
    )
    with pytest.raises(RuntimeError):
        legacy_quote.save()
