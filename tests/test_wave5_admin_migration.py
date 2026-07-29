from pathlib import Path

import pytest

from apps.business_core.models import BusinessCustomer, BusinessProduct, InventoryWarehouse
from apps.business_core.services import InventoryService
from apps.foundation.models import FoundationUser
from apps.foundation.services import FoundationAuthService, FoundationUserService
from apps.transaction_domain.models import TransactionHistory, TransactionOrder
from apps.transaction_domain.services import OrderService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def admin_user():
    """Create or reuse a Django-owned admin user."""
    existing = FoundationUser.objects.filter(email="wave5-admin@example.com").first()
    if existing:
        return existing
    return FoundationUserService().create_user(
        email="wave5-admin@example.com",
        full_name="Wave 5 Admin",
        password="SecurePass123!",
        role_name="admin",
    )


@pytest.fixture
def viewer_user():
    """Create or reuse a Django-owned viewer user."""
    existing = FoundationUser.objects.filter(email="wave5-viewer@example.com").first()
    if existing:
        return existing
    return FoundationUserService().create_user(
        email="wave5-viewer@example.com",
        full_name="Wave 5 Viewer",
        password="SecurePass123!",
        role_name="viewer",
    )


def bearer_header(user):
    """Create a Bearer token header for admin API tests."""
    token, _token_row = FoundationAuthService().login(user.email, "SecurePass123!")
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.mark.django_db
def test_admin_login_returns_token_and_navigation(client, admin_user):
    response = client.post(
        "/api/v1/admin/login/",
        data={"email": admin_user.email, "password": "SecurePass123!"},
        content_type="application/json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["token"]
    assert body["data"]["user"]["email"] == admin_user.email
    assert any(item["module"] == "products" for item in body["data"]["navigation"])


@pytest.mark.django_db
def test_admin_dashboard_requires_auth_and_returns_counts(client, admin_user):
    denied = client.get("/api/v1/admin/dashboard/")
    allowed = client.get("/api/v1/admin/dashboard/", **bearer_header(admin_user))

    assert denied.status_code == 403
    assert allowed.status_code == 200
    assert allowed.json()["data"]["ownership"] == "django"
    assert "products" in allowed.json()["data"]["metrics"]


@pytest.mark.django_db
def test_admin_permission_control_blocks_viewer_writes(client, viewer_user):
    response = client.post(
        "/api/v1/admin/products/",
        data={
            "name": "Viewer Blocked Product",
            "slug": "viewer-blocked-product",
        },
        content_type="application/json",
        **bearer_header(viewer_user),
    )

    assert response.status_code == 403
    assert response.json()["success"] is False


@pytest.mark.django_db
def test_admin_product_crud_uses_django_business_service(client, admin_user):
    headers = bearer_header(admin_user)
    create_response = client.post(
        "/api/v1/admin/products/",
        data={
            "name": "Admin Product",
            "slug": "admin-product-wave5",
            "sku": "ADM-001",
            "price": "33.00",
            "status": "draft",
            "short_description": "Admin-created product",
            "description": "Created by Django admin API.",
            "main_image": "/media/products/admin.jpg",
        },
        content_type="application/json",
        **headers,
    )
    product_id = create_response.json()["data"]["id"]
    update_response = client.put(
        f"/api/v1/admin/products/{product_id}/",
        data={"status": "published", "price": "44.00"},
        content_type="application/json",
        **headers,
    )

    assert create_response.status_code == 201
    assert BusinessProduct.objects.filter(id=product_id).exists()
    assert update_response.status_code == 200
    assert update_response.json()["data"]["status"] == "published"


@pytest.mark.django_db
def test_admin_customer_crud_uses_django_business_service(client, admin_user):
    headers = bearer_header(admin_user)
    create_response = client.post(
        "/api/v1/admin/customers/",
        data={
            "company_name": "Admin Customer Co",
            "contact_name": "Admin Contact",
            "email": "admin-customer-wave5@example.com",
            "phone": "0900000005",
            "status": "lead",
        },
        content_type="application/json",
        **headers,
    )
    customer_id = create_response.json()["data"]["id"]
    update_response = client.put(
        f"/api/v1/admin/customers/{customer_id}/",
        data={"status": "active", "notes": "Managed by Django admin API."},
        content_type="application/json",
        **headers,
    )

    assert create_response.status_code == 201
    assert BusinessCustomer.objects.filter(id=customer_id).exists()
    assert update_response.status_code == 200
    assert update_response.json()["data"]["status"] == "active"


@pytest.mark.django_db
def test_admin_inventory_operations_use_django_inventory_service(client, admin_user):
    headers = bearer_header(admin_user)
    product = BusinessProduct.objects.create(name="Admin Inventory Product", slug="admin-inventory-product")
    warehouse_response = client.post(
        "/api/v1/admin/inventory/warehouses/",
        data={"code": "W5A", "name": "Wave 5 Admin Warehouse"},
        content_type="application/json",
        **headers,
    )
    warehouse_id = warehouse_response.json()["data"]["id"]
    item_response = client.post(
        "/api/v1/admin/inventory/items/",
        data={"product_id": product.id, "warehouse_id": warehouse_id, "quantity": "10"},
        content_type="application/json",
        **headers,
    )
    item_id = item_response.json()["data"]["id"]
    adjust_response = client.post(
        f"/api/v1/admin/inventory/items/{item_id}/adjust/",
        data={"quantity_delta": "-2", "transaction_type": "issue", "reason": "Admin issue"},
        content_type="application/json",
        **headers,
    )

    assert warehouse_response.status_code == 201
    assert InventoryWarehouse.objects.filter(id=warehouse_id).exists()
    assert item_response.status_code == 201
    assert adjust_response.status_code == 200
    assert adjust_response.json()["data"]["quantity"] == "8.00"


@pytest.mark.django_db
def test_admin_order_workflow_and_transaction_history(client, admin_user):
    headers = bearer_header(admin_user)
    customer = BusinessCustomer.objects.create(contact_name="Admin Order Customer")
    product = BusinessProduct.objects.create(name="Admin Order Product", slug="admin-order-product")
    warehouse = InventoryWarehouse.objects.create(code="W5O", name="Wave 5 Order Warehouse")
    inventory_item = InventoryService().create_item(product=product, warehouse=warehouse, quantity="20")

    order_response = client.post(
        "/api/v1/admin/orders/",
        data={
            "customer_id": customer.id,
            "project_name": "Admin order",
            "items": [
                {
                    "product_id": product.id,
                    "inventory_item_id": inventory_item.id,
                    "quantity": 2,
                    "unit_price": "20.00",
                }
            ],
        },
        content_type="application/json",
        **headers,
    )
    order_id = order_response.json()["data"]["id"]
    workflow_response = client.post(
        "/api/v1/admin/workflows/",
        data={"order_id": order_id, "target_status": "approved", "note": "Admin approved"},
        content_type="application/json",
        **headers,
    )
    history_response = client.get("/api/v1/admin/transactions/", **headers)

    assert order_response.status_code == 201
    assert TransactionOrder.objects.filter(id=order_id).exists()
    assert workflow_response.status_code == 200
    assert workflow_response.json()["data"]["status"] == "approved"
    assert history_response.status_code == 200
    assert TransactionHistory.objects.filter(order_id=order_id).exists()


@pytest.mark.django_db
def test_admin_permissions_endpoint_returns_roles(client, admin_user):
    response = client.get("/api/v1/admin/permissions/", **bearer_header(admin_user))

    assert response.status_code == 200
    role_names = [role["name"] for role in response.json()["data"]]
    assert "admin" in role_names


def test_legacy_admin_compatibility_files_remain():
    """Wave 5 must not delete the legacy admin surface."""
    assert (PROJECT_ROOT / "backend" / "app.py").exists()
    assert (PROJECT_ROOT / "backend" / "services" / "cms_service.py").exists()
    assert (PROJECT_ROOT / "backend" / "repositories" / "cms_repository.py").exists()
