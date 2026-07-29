from pathlib import Path
import re

import pytest
from django.test import Client

from apps.business_core.models import BusinessCustomer, BusinessProduct, InventoryItem, InventoryWarehouse
from apps.business_core.services import InventoryService
from apps.foundation.models import FoundationUser
from apps.foundation.services import FoundationUserService
from apps.transaction_domain.models import TransactionHistory, TransactionOrder


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def admin_user():
    """Create or reuse a Django-owned admin user for UI tests."""
    existing = FoundationUser.objects.filter(email="wave6-admin@example.com").first()
    if existing:
        return existing
    return FoundationUserService().create_user(
        email="wave6-admin@example.com",
        full_name="Wave 6 Admin",
        password="SecurePass123!",
        role_name="admin",
    )


@pytest.fixture
def viewer_user():
    """Create or reuse a Django-owned read-only user for UI tests."""
    existing = FoundationUser.objects.filter(email="wave6-viewer@example.com").first()
    if existing:
        return existing
    return FoundationUserService().create_user(
        email="wave6-viewer@example.com",
        full_name="Wave 6 Viewer",
        password="SecurePass123!",
        role_name="viewer",
    )


def ui_login(client, user):
    """Log in through the browser-facing Django admin UI."""
    return client.post(
        "/admin/login/",
        data={"email": user.email, "password": "SecurePass123!"},
        follow=True,
    )


def csrf_token_from(response):
    """Read a CSRF token from rendered HTML."""
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode())
    assert match
    return match.group(1)


@pytest.mark.django_db
def test_admin_ui_login_sets_session_and_renders_dashboard(client, admin_user):
    response = ui_login(client, admin_user)

    assert response.status_code == 200
    assert b"Django-owned admin UI" in response.content
    assert client.session.get("foundation_admin_token")


@pytest.mark.django_db
def test_admin_ui_requires_login_for_dashboard(client):
    response = client.get("/admin/")

    assert response.status_code == 302
    assert response["Location"].endswith("/admin/login/")


@pytest.mark.django_db
def test_admin_ui_csrf_protection_on_login(admin_user):
    csrf_client = Client(enforce_csrf_checks=True)
    response = csrf_client.post(
        "/admin/login/",
        data={"email": admin_user.email, "password": "SecurePass123!"},
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_ui_csrf_login_success_with_token(admin_user):
    csrf_client = Client(enforce_csrf_checks=True)
    login_page = csrf_client.get("/admin/login/")
    token = csrf_token_from(login_page)
    response = csrf_client.post(
        "/admin/login/",
        data={
            "email": admin_user.email,
            "password": "SecurePass123!",
            "csrfmiddlewaretoken": token,
        },
        follow=True,
    )

    assert response.status_code == 200
    assert b"Dashboard" in response.content


@pytest.mark.django_db
def test_admin_ui_product_create_and_update(client, admin_user):
    ui_login(client, admin_user)
    create_response = client.post(
        "/admin/products/",
        data={
            "name": "Wave 6 UI Product",
            "slug": "wave-6-ui-product",
            "sku": "W6-UI",
            "price": "12.50",
            "status": "draft",
        },
        follow=True,
    )
    product = BusinessProduct.objects.get(slug="wave-6-ui-product")
    update_response = client.post(
        f"/admin/products/{product.id}/",
        data={
            "name": "Wave 6 UI Product Updated",
            "slug": product.slug,
            "sku": "W6-UI",
            "price": "14.50",
            "status": "published",
            "sort_order": "2",
        },
        follow=True,
    )
    product.refresh_from_db()

    assert create_response.status_code == 200
    assert update_response.status_code == 200
    assert product.name == "Wave 6 UI Product Updated"
    assert product.status == "published"


@pytest.mark.django_db
def test_admin_ui_viewer_cannot_create_product(client, viewer_user):
    ui_login(client, viewer_user)
    response = client.post(
        "/admin/products/",
        data={"name": "Blocked UI Product", "slug": "blocked-ui-product"},
        follow=True,
    )

    assert response.status_code == 200
    assert not BusinessProduct.objects.filter(slug="blocked-ui-product").exists()
    assert b"Missing permission" in response.content


@pytest.mark.django_db
def test_admin_ui_customer_create_and_update(client, admin_user):
    ui_login(client, admin_user)
    client.post(
        "/admin/customers/",
        data={
            "company_name": "Wave 6 Customer",
            "contact_name": "Wave Contact",
            "email": "wave6-customer@example.com",
            "status": "lead",
        },
        follow=True,
    )
    customer = BusinessCustomer.objects.get(email="wave6-customer@example.com")
    response = client.post(
        f"/admin/customers/{customer.id}/",
        data={
            "company_name": "Wave 6 Customer Co",
            "contact_name": "Wave Contact",
            "email": "wave6-customer@example.com",
            "status": "active",
            "notes": "Updated from Django UI",
        },
        follow=True,
    )
    customer.refresh_from_db()

    assert response.status_code == 200
    assert customer.status == "active"
    assert customer.notes == "Updated from Django UI"


@pytest.mark.django_db
def test_admin_ui_inventory_create_and_adjust(client, admin_user):
    ui_login(client, admin_user)
    product = BusinessProduct.objects.create(name="Wave 6 Inventory Product", slug="wave-6-inventory-product")
    warehouse_response = client.post(
        "/admin/inventory/",
        data={
            "form_name": "warehouse",
            "warehouse-code": "W6UI",
            "warehouse-name": "Wave 6 UI Warehouse",
            "warehouse-location": "Test",
            "warehouse-is_active": "on",
        },
        follow=True,
    )
    warehouse = InventoryWarehouse.objects.get(code="W6UI")
    item_response = client.post(
        "/admin/inventory/",
        data={
            "form_name": "item",
            "item-product": product.id,
            "item-warehouse": warehouse.id,
            "item-quantity": "7",
            "item-reorder_point": "1",
        },
        follow=True,
    )
    item = InventoryItem.objects.get(product=product, warehouse=warehouse)
    adjust_response = client.post(
        f"/admin/inventory/items/{item.id}/adjust/",
        data={"quantity_delta": "3", "transaction_type": "receipt", "reason": "UI test"},
        follow=True,
    )
    item.refresh_from_db()

    assert warehouse_response.status_code == 200
    assert item_response.status_code == 200
    assert adjust_response.status_code == 200
    assert str(item.quantity) == "10.00"


@pytest.mark.django_db
def test_admin_ui_order_workflow_and_transaction_history(client, admin_user):
    ui_login(client, admin_user)
    customer = BusinessCustomer.objects.create(contact_name="Wave 6 Order Customer")
    product = BusinessProduct.objects.create(name="Wave 6 Order Product", slug="wave-6-order-product")
    warehouse = InventoryWarehouse.objects.create(code="W6ORD", name="Wave 6 Order Warehouse")
    inventory_item = InventoryService().create_item(product=product, warehouse=warehouse, quantity="5")

    order_response = client.post(
        "/admin/orders/",
        data={
            "customer": customer.id,
            "project_name": "Wave 6 UI Order",
            "product": product.id,
            "inventory_item": inventory_item.id,
            "quantity": "1",
            "unit_price": "20",
        },
        follow=True,
    )
    order = TransactionOrder.objects.get(project_name="Wave 6 UI Order")
    workflow_response = client.post(
        "/admin/workflows/",
        data={"order": order.id, "target_status": "approved", "note": "Approved from UI"},
        follow=True,
    )
    history_response = client.get("/admin/transactions/")
    order.refresh_from_db()

    assert order_response.status_code == 200
    assert workflow_response.status_code == 200
    assert history_response.status_code == 200
    assert order.status == "approved"
    assert TransactionHistory.objects.filter(order=order).exists()


def test_wave6_legacy_admin_compatibility_files_remain():
    """Wave 6 cuts over Django UI without deleting legacy admin code."""
    assert (PROJECT_ROOT / "backend" / "app.py").exists()
    assert (PROJECT_ROOT / "backend" / "services" / "cms_service.py").exists()
    assert (PROJECT_ROOT / "backend" / "repositories" / "cms_repository.py").exists()
