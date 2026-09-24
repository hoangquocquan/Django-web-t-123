import sqlite3

import pytest

from apps.business_core.models import (
    BusinessCustomer,
    BusinessProduct,
    InventoryItem,
    InventoryTransaction,
    InventoryWarehouse,
)
from apps.business_core.services import (
    BusinessCustomerService,
    BusinessProductService,
    InventoryService,
)
from apps.catalog.models import Product as LegacyProduct
from apps.catalog.repositories.product_repository import ProductRepository
from apps.crm.models import Customer as LegacyCustomer
from apps.crm.repositories.customer_repository import CustomerRepository
from apps.foundation.models import FoundationUser
from apps.foundation.services import FoundationAuthService, FoundationUserService
from tests.legacy_sqlite_helpers import create_legacy_sqlite_fixture


@pytest.fixture
def legacy_db(tmp_path):
    """Return a read-only copied legacy database path."""
    return create_legacy_sqlite_fixture(
        tmp_path / "legacy_database" / "mecprecision-test.sqlite"
    )


def count_legacy_rows(legacy_db, table_name):
    """Count rows in a copied legacy table without writing to it."""
    connection_uri = f"file:{legacy_db.as_posix()}?mode=ro"
    with sqlite3.connect(connection_uri, uri=True) as legacy_connection:
        return legacy_connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


@pytest.fixture
def foundation_admin():
    """Create or reuse one Django-owned admin user for protected API calls."""
    existing = FoundationUser.objects.filter(email="wave2-admin@example.com").first()
    if existing:
        return existing
    return FoundationUserService().create_user(
        email="wave2-admin@example.com",
        full_name="Wave 2 Admin",
        password="SecurePass123!",
        role_name="admin",
    )


def bearer_header(user):
    """Create one Bearer token header for the Django-owned foundation auth API."""
    token, _token_row = FoundationAuthService().login(user.email, "SecurePass123!")
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.mark.django_db
def test_wave2_migrations_seed_products_customers_and_inventory():
    assert BusinessProduct.objects.filter(legacy_product_id__isnull=False).count() >= 1
    assert BusinessCustomer.objects.filter(legacy_customer_id__isnull=False).count() >= 1
    assert InventoryWarehouse.objects.filter(code="MAIN").exists()
    assert InventoryItem.objects.select_related("product", "warehouse").count() >= 1


@pytest.mark.django_db
def test_business_product_service_owns_new_product_writes():
    product = BusinessProductService().create_product(
        name="Django Owned CNC Shaft",
        slug="django-owned-cnc-shaft",
        sku="DJ-CNC-001",
        price="120.50",
        status="published",
        short_description="Precision shaft owned by Django.",
        description="Created by Wave 2 service.",
        main_image="/media/products/shaft.jpg",
        category_name="CNC",
    )

    assert product.id
    assert product.legacy_product_id is None
    assert BusinessProduct.objects.filter(slug="django-owned-cnc-shaft").exists()


@pytest.mark.django_db
def test_business_customer_service_owns_new_customer_writes():
    customer = BusinessCustomerService().create_customer(
        company_name="Django Manufacturing Co",
        contact_name="Nguyen Van A",
        email="customer-wave2@example.com",
        phone="0900000001",
        country="Vietnam",
        status="lead",
    )

    assert customer.id
    assert customer.legacy_customer_id is None
    assert customer.status == "lead"


@pytest.mark.django_db
def test_inventory_service_adjusts_stock_transactionally():
    product = BusinessProduct.objects.first()
    warehouse = InventoryWarehouse.objects.first()
    item = InventoryService().create_item(
        product=product,
        warehouse=InventoryWarehouse.objects.create(code="QA", name="QA Warehouse"),
        quantity="5",
        reorder_point="2",
    )

    updated = InventoryService().adjust_stock(
        item=item,
        quantity_delta="3",
        transaction_type="receipt",
        reason="Incoming demo stock",
        created_by="wave2-admin@example.com",
    )

    assert product
    assert warehouse
    assert updated.quantity == 8
    assert InventoryTransaction.objects.filter(item=item, transaction_type="receipt").exists()


@pytest.mark.django_db
def test_inventory_service_blocks_negative_stock():
    product = BusinessProduct.objects.first()
    warehouse = InventoryWarehouse.objects.create(code="NEG", name="Negative Test")
    item = InventoryService().create_item(product=product, warehouse=warehouse, quantity="1")

    with pytest.raises(Exception):
        InventoryService().adjust_stock(item=item, quantity_delta="-2", transaction_type="issue")

    item.refresh_from_db()
    assert item.quantity == 1


@pytest.mark.django_db
def test_business_product_api_requires_foundation_permission(client):
    response = client.get("/api/v1/business/products/")

    assert response.status_code == 403
    assert response.json()["success"] is False


@pytest.mark.django_db
def test_business_product_api_create_and_update(client, foundation_admin):
    headers = bearer_header(foundation_admin)
    create_response = client.post(
        "/api/v1/business/products/",
        data={
            "name": "API Business Product",
            "slug": "api-business-product",
            "sku": "API-BIZ-001",
            "price": "88.00",
            "status": "draft",
            "short_description": "Created through Django-owned API.",
            "description": "Wave 2 product API test.",
            "main_image": "/media/products/api.jpg",
        },
        content_type="application/json",
        **headers,
    )
    product_id = create_response.json()["data"]["id"]
    update_response = client.put(
        f"/api/v1/business/products/{product_id}/",
        data={"status": "published", "price": "99.00"},
        content_type="application/json",
        **headers,
    )

    assert create_response.status_code == 201
    assert update_response.status_code == 200
    assert update_response.json()["data"]["status"] == "published"
    assert update_response.json()["data"]["price"] == "99.00"


@pytest.mark.django_db
def test_business_customer_api_create_and_update(client, foundation_admin):
    headers = bearer_header(foundation_admin)
    create_response = client.post(
        "/api/v1/business/customers/",
        data={
            "company_name": "API Customer Co",
            "contact_name": "Tran Thi B",
            "email": "api-customer@example.com",
            "phone": "0900000002",
            "country": "Vietnam",
            "status": "lead",
        },
        content_type="application/json",
        **headers,
    )
    customer_id = create_response.json()["data"]["id"]
    update_response = client.put(
        f"/api/v1/business/customers/{customer_id}/",
        data={"status": "active", "notes": "Converted from lead."},
        content_type="application/json",
        **headers,
    )

    assert create_response.status_code == 201
    assert update_response.status_code == 200
    assert update_response.json()["data"]["status"] == "active"
    assert update_response.json()["data"]["notes"] == "Converted from lead."


@pytest.mark.django_db
def test_inventory_api_adjusts_stock(client, foundation_admin):
    headers = bearer_header(foundation_admin)
    product = BusinessProduct.objects.first()
    warehouse = InventoryWarehouse.objects.create(code="API", name="API Warehouse")
    item = InventoryService().create_item(product=product, warehouse=warehouse, quantity="10")

    response = client.post(
        f"/api/v1/inventory/items/{item.id}/adjust/",
        data={"quantity_delta": "-3", "transaction_type": "issue", "reason": "Demo issue"},
        content_type="application/json",
        **headers,
    )

    assert response.status_code == 200
    assert response.json()["data"]["quantity"] == "7.00"


@pytest.mark.django_db
def test_legacy_product_and_customer_compatibility_remains_read_only(legacy_db):
    assert LegacyProduct._meta.managed is False
    assert LegacyCustomer._meta.managed is False
    assert ProductRepository().list_products()._db == "legacy"
    assert CustomerRepository().list_customers()._db == "legacy"
    assert count_legacy_rows(legacy_db, "products") >= 1
    assert count_legacy_rows(legacy_db, "customers") >= 1

    legacy_product = LegacyProduct(
        id=999,
        category_id=1,
        name="Legacy Product",
        slug="legacy-product-write-blocked",
        short_description="Legacy",
        description="Legacy",
        main_image="",
        created_at="2026-01-01 00:00:00",
        updated_at="2026-01-01 00:00:00",
    )
    legacy_customer = LegacyCustomer(
        id=999,
        contact_name="Legacy Customer",
        created_at="2026-01-01 00:00:00",
    )
    with pytest.raises(RuntimeError):
        legacy_product.save()
    with pytest.raises(RuntimeError):
        legacy_customer.save()
