"""Tests for Phase 9.1 read-only business API cutover."""

from pathlib import Path

import pytest

from apps.accounts.repositories.auth_repository import AdminUserRepository
from apps.catalog.services.catalog_service import CatalogService
from apps.cms.services.cms_service import CmsService
from apps.crm.services.crm_service import CrmService
from apps.sales.services.quotation_service import QuotationService


@pytest.mark.parametrize(
    "url",
    [
        "/api/v1/catalog/products/",
        "/api/v1/catalog/categories/",
        "/api/v1/catalog/materials/",
        "/api/v1/crm/customers/",
        "/api/v1/crm/contact-requests/",
        "/api/v1/sales/quotes/",
        "/api/v1/cms/pages/",
        "/api/v1/cms/menu/",
        "/api/v1/auth/permissions/",
    ],
)
def test_read_only_business_list_endpoints_return_success(client, legacy_db, url):
    """List endpoints must return a consistent success envelope."""
    response = client.get(url)
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert "data" in body


def test_catalog_product_detail_endpoint_uses_legacy_data(client, legacy_db):
    """Product detail endpoint exposes product data and gallery image list."""
    product = CatalogService().list_products().first()

    response = client.get(f"/api/v1/catalog/products/{product.id}/")
    body = response.json()

    assert response.status_code == 200
    assert body["data"]["id"] == product.id
    assert "category" in body["data"]
    assert "images" in body["data"]


def test_crm_customer_detail_endpoint_includes_notes(client, legacy_db):
    """Customer detail endpoint returns notes through the CRM service."""
    customer = CrmService().list_customer_profiles().first()

    response = client.get(f"/api/v1/crm/customers/{customer.id}/")
    body = response.json()

    assert response.status_code == 200
    assert body["data"]["id"] == customer.id
    assert "notes" in body["data"]


def test_sales_quote_detail_and_files_endpoints(client, legacy_db):
    """Sales endpoints expose quote detail and file metadata as read-only JSON."""
    quote = QuotationService().list_quotes().first()

    detail_response = client.get(f"/api/v1/sales/quotes/{quote.id}/")
    files_response = client.get(f"/api/v1/sales/quotes/{quote.id}/files/")

    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["id"] == quote.id
    assert "items" in detail_response.json()["data"]
    assert "files" in detail_response.json()["data"]
    assert files_response.status_code == 200
    assert "results" in files_response.json()["data"]


def test_cms_page_detail_endpoint_uses_slug(client, legacy_db):
    """CMS page detail endpoint resolves published pages by slug."""
    page = CmsService().list_public_pages().first()

    response = client.get(f"/api/v1/cms/pages/{page.slug}/")
    body = response.json()

    assert response.status_code == 200
    assert body["data"]["slug"] == page.slug


def test_auth_profile_does_not_expose_password_hash(client, legacy_db):
    """Auth preparation endpoint must not expose password hashes or tokens."""
    admin_user = AdminUserRepository().list_users().first()

    response = client.get(f"/api/v1/auth/profile/?admin_id={admin_user.id}")
    body = response.json()

    assert response.status_code == 200
    assert body["data"]["id"] == admin_user.id
    assert "password_hash" not in body["data"]
    assert "token" not in body["data"]


def test_business_api_rejects_write_methods(client, legacy_db):
    """Phase 9.1 APIs are read-only and must reject write attempts."""
    response = client.post(
        "/api/v1/catalog/products/",
        data={"name": "Should not write"},
        content_type="application/json",
    )

    assert response.status_code == 403
    assert "detail" in response.json()


def test_missing_business_resource_returns_consistent_404(client, legacy_db):
    """Missing detail routes must return a consistent JSON error."""
    response = client.get("/api/v1/catalog/products/999999/")
    body = response.json()

    assert response.status_code == 404
    assert body["success"] is False
    assert body["error"]["code"] == "not_found"


def test_api_views_do_not_access_orm_directly():
    """API view modules must call services instead of direct ORM managers."""
    views_root = Path(__file__).resolve().parents[1] / "views"
    view_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in views_root.glob("*.py")
        if path.name != "__init__.py"
    )

    assert ".objects" not in view_source
    assert ".using(" not in view_source
