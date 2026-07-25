"""Production readiness tests for Phase 9.2 API hardening."""

from django.db import connections
from django.test.utils import CaptureQueriesContext
import pytest


LIST_ENDPOINTS = [
    "/api/v1/catalog/products/",
    "/api/v1/catalog/categories/",
    "/api/v1/catalog/materials/",
    "/api/v1/crm/customers/",
    "/api/v1/crm/contact-requests/",
    "/api/v1/sales/quotes/",
    "/api/v1/cms/pages/",
    "/api/v1/cms/menu/",
]


@pytest.mark.parametrize("url", LIST_ENDPOINTS)
def test_list_endpoints_return_pagination_schema(client, legacy_db, url):
    """List APIs must expose pagination metadata for production clients."""
    response = client.get(f"{url}?limit=1&offset=0")
    data = response.json()["data"]

    assert response.status_code == 200
    assert set(data.keys()) == {"count", "limit", "offset", "next_offset", "results"}
    assert data["limit"] == 1
    assert data["offset"] == 0
    assert len(data["results"]) <= 1


def test_invalid_pagination_returns_consistent_400(client, legacy_db):
    """Invalid pagination input should fail before reaching business logic."""
    response = client.get("/api/v1/catalog/products/?limit=abc")
    body = response.json()

    assert response.status_code == 400
    assert body["success"] is False
    assert body["error"]["code"] == "invalid_pagination"


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
@pytest.mark.parametrize(
    "url",
    [
        "/api/v1/crm/customers/",
        "/api/v1/cms/pages/",
        "/api/v1/auth/profile/",
    ],
)
def test_unsafe_methods_are_blocked_across_business_apis(client, legacy_db, method, url):
    """Non-replacement business APIs still block unsafe methods."""
    request_method = getattr(client, method)
    response = request_method(url, data={}, content_type="application/json")

    assert response.status_code in {403, 405}


def test_phase11_1_1_write_replacements_are_validation_gated(client, legacy_db):
    """Explicit replacement write routes exist but reject unsafe empty payloads."""
    product_response = client.post(
        "/api/v1/catalog/products/",
        data={},
        content_type="application/json",
    )
    quote_response = client.post(
        "/api/v1/sales/quotes/",
        data={},
        content_type="application/json",
    )

    assert product_response.status_code == 400
    assert product_response.json()["error"]["code"] == "permission_denied"
    assert quote_response.status_code == 400
    assert quote_response.json()["error"]["code"] == "validation_error"


def test_catalog_product_list_query_count_is_bounded(client, legacy_db):
    """Product list should use count plus one joined page query."""
    with CaptureQueriesContext(connections["legacy"]) as captured:
        response = client.get("/api/v1/catalog/products/?limit=5")

    assert response.status_code == 200
    assert len(captured) <= 2


def test_crm_customer_list_query_count_is_bounded(client, legacy_db):
    """Customer list may use count, page query and notes prefetch."""
    with CaptureQueriesContext(connections["legacy"]) as captured:
        response = client.get("/api/v1/crm/customers/?limit=5")

    assert response.status_code == 200
    assert len(captured) <= 3


def test_sensitive_auth_words_do_not_appear_in_auth_api_payload(client, legacy_db):
    """Auth preparation endpoints must not leak credential/session internals."""
    response = client.get("/api/v1/auth/profile/?admin_id=1")
    serialized_payload = str(response.json()).lower()

    assert response.status_code == 200
    assert "password_hash" not in serialized_payload
    assert "session_id" not in serialized_payload
    assert "reset_token" not in serialized_payload
    assert "two_factor_code" not in serialized_payload


def test_legacy_database_remains_read_only_after_api_requests(client, legacy_db):
    """API reads should not mutate the copied legacy database fixture."""
    before_size = legacy_db.stat().st_size

    client.get("/api/v1/catalog/products/?limit=2")
    client.get("/api/v1/crm/contact-requests/?limit=2")
    client.get("/api/v1/sales/quotes/?limit=2")

    assert legacy_db.stat().st_size == before_size
