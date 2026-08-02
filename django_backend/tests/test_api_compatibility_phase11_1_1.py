"""Compatibility tests for Phase 11.1.1 Django API replacements."""

import pytest
from apps.api.services.replacement_submission_service import reset_submissions

REPLACEMENT_GET_ENDPOINTS = [
    "/api/v1/public/home/",
    "/api/v1/catalog/capabilities/",
    "/api/v1/news/",
    "/api/v1/openapi.json",
    "/api/v1/version/",
    "/api/v1/demo/aws/",
    "/api/v1/demo/external/weather/",
]


@pytest.fixture(autouse=True)
def clear_submission_store():
    """Keep write-intent tests isolated from each other."""
    reset_submissions()
    yield
    reset_submissions()


@pytest.mark.parametrize("url", REPLACEMENT_GET_ENDPOINTS)
def test_phase11_1_1_get_replacements_are_available(client, legacy_db, url):
    """Remaining legacy GET APIs should have Django replacement endpoints."""
    response = client.get(url)
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert "data" in body


def test_contact_write_replacement_validates_and_accepts_submission(client):
    """Django replacement for legacy POST /api/contact accepts valid data."""
    response = client.post(
        "/api/v1/crm/contact-requests/",
        data={
            "name": "Nguyen Van A",
            "email": "a@example.com",
            "message": "Tôi cần tư vấn gia công CNC.",
            "captcha_answer": "7",
        },
        content_type="application/json",
    )
    body = response.json()

    assert response.status_code == 201
    assert body["success"] is True
    assert body["data"]["submission"]["legacy_endpoint"] == "/api/contact"


def test_contact_write_replacement_rejects_invalid_payload(client):
    """Missing name/contact data should return consistent validation error."""
    response = client.post(
        "/api/v1/crm/contact-requests/",
        data={"message": "Thiếu thông tin"},
        content_type="application/json",
    )
    body = response.json()

    assert response.status_code == 400
    assert body["success"] is False
    assert body["error"]["code"] == "validation_error"


def test_quote_write_replacement_validates_and_accepts_submission(client):
    """Django replacement for legacy POST /api/quote-request accepts valid data."""
    response = client.post(
        "/api/v1/sales/quotes/",
        data={
            "name": "Tran Thi B",
            "company": "Demo Precision",
            "email": "quote@example.com",
            "product": "Trục CNC",
            "quantity": 10,
        },
        content_type="application/json",
    )
    body = response.json()

    assert response.status_code == 201
    assert body["data"]["submission"]["legacy_endpoint"] == "/api/quote-request"


def test_product_write_replacement_requires_admin_token(client):
    """Product writes are protected even though the replacement route exists."""
    response = client.post(
        "/api/v1/catalog/products/",
        data={
            "category_id": 1,
            "name": "Demo product",
            "short_description": "Short",
            "description": "Long",
            "main_image": "/images/demo.jpg",
        },
        content_type="application/json",
    )
    body = response.json()

    assert response.status_code == 400
    assert body["success"] is False
    assert body["error"]["code"] == "permission_denied"


def test_product_write_replacement_accepts_admin_token(client):
    """Admin token allows the product create replacement contract."""
    response = client.post(
        "/api/v1/catalog/products/",
        data={
            "category_id": 1,
            "name": "Demo product",
            "short_description": "Short",
            "description": "Long",
            "main_image": "/images/demo.jpg",
            "status": "draft",
        },
        HTTP_X_ADMIN_TOKEN="dev-admin-token",
        content_type="application/json",
    )
    body = response.json()

    assert response.status_code == 201
    assert body["data"]["submission"]["submission_type"] == "product"


def test_product_update_and_delete_replacements_are_admin_protected(client):
    """PUT and DELETE replacement routes accept admin-approved write intents."""
    update_response = client.put(
        "/api/v1/catalog/products/1/",
        data={"name": "Updated demo product"},
        HTTP_X_ADMIN_TOKEN="dev-admin-token",
        content_type="application/json",
    )
    delete_response = client.delete(
        "/api/v1/catalog/products/1/",
        HTTP_X_ADMIN_TOKEN="dev-admin-token",
        content_type="application/json",
    )

    assert update_response.status_code == 200
    assert update_response.json()["data"]["submission"]["operation"] == "PUT"
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["submission"]["operation"] == "DELETE"


def test_ai_chat_replacement_requires_authentication(client):
    """AI chat replacement must not expose local inference anonymously."""
    response = client.post(
        "/api/v1/ai/chat/",
        data={"question": "MecPrecision có gia công CNC không?"},
        content_type="application/json",
    )
    body = response.json()

    assert response.status_code == 403
    assert body["success"] is False
    assert body["error"]["code"] == "permission_denied"


def test_unrelated_write_endpoints_remain_blocked(client, legacy_db):
    """Phase 11.1.1 opens only explicit legacy replacement write routes."""
    response = client.post(
        "/api/v1/cms/pages/",
        data={"title": "Should stay blocked"},
        content_type="application/json",
    )

    assert response.status_code in {401, 403, 405}
