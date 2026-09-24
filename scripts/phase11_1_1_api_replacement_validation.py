"""Validate Phase 11.1.1 Django API replacement coverage.

The script uses Django's test client so it does not require a running server.
It validates endpoint availability, response envelopes, validation behavior and
permission gates for legacy API replacements.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DJANGO_ROOT = PROJECT_ROOT / "django_backend"
sys.path.insert(0, str(DJANGO_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")

import django  # noqa: E402


django.setup()

from django.conf import settings  # noqa: E402
from django.test import Client  # noqa: E402

if "testserver" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append("testserver")


GET_REPLACEMENTS = [
    ("GET /api/home", "/api/v1/public/home/"),
    ("GET /api/capabilities", "/api/v1/catalog/capabilities/"),
    ("GET /api/news", "/api/v1/news/"),
    ("GET /api/openapi.json", "/api/v1/openapi.json"),
    ("GET /api/version", "/api/v1/version/"),
    ("GET /api/aws-demo", "/api/v1/demo/aws/"),
    ("GET /api/external/weather", "/api/v1/demo/external/weather/"),
]

WRITE_REPLACEMENTS = [
    (
        "POST /api/contact",
        "post",
        "/api/v1/crm/contact-requests/",
        {"name": "Validation Contact", "email": "contact@example.com", "message": "Need CNC"},
        201,
        {},
    ),
    (
        "POST /api/quote-request",
        "post",
        "/api/v1/sales/quotes/",
        {"name": "Validation Quote", "email": "quote@example.com", "product": "Trục CNC"},
        201,
        {},
    ),
    (
        "POST /api/ai/chat",
        "post",
        "/api/v1/ai/chat/",
        {"question": "MecPrecision có gia công CNC không?"},
        200,
        {},
    ),
    (
        "POST /api/products",
        "post",
        "/api/v1/catalog/products/",
        {
            "category_id": 1,
            "name": "Validation product",
            "short_description": "Short",
            "description": "Long",
            "main_image": "/images/demo.jpg",
            "status": "draft",
        },
        201,
        {"HTTP_X_ADMIN_TOKEN": "dev-admin-token"},
    ),
    (
        "PUT /api/products/{id}",
        "put",
        "/api/v1/catalog/products/1/",
        {"name": "Validation update"},
        200,
        {"HTTP_X_ADMIN_TOKEN": "dev-admin-token"},
    ),
    (
        "DELETE /api/products/{id}",
        "delete",
        "/api/v1/catalog/products/1/",
        {},
        200,
        {"HTTP_X_ADMIN_TOKEN": "dev-admin-token"},
    ),
]


def _json_response(response):
    """Return decoded JSON while keeping error context readable."""
    try:
        return response.json()
    except ValueError:
        return {"success": False, "raw": response.content.decode("utf-8", errors="ignore")}


def validate_get(client, legacy_name, url):
    """Validate one GET replacement endpoint."""
    response = client.get(url)
    body = _json_response(response)
    passed = response.status_code == 200 and body.get("success") is True and "data" in body
    return {
        "legacy_route": legacy_name,
        "django_route": url,
        "status_code": response.status_code,
        "passed": passed,
    }


def validate_write(client, legacy_name, method, url, payload, expected_status, headers):
    """Validate one write replacement endpoint."""
    request_method = getattr(client, method)
    response = request_method(
        url,
        data=payload,
        content_type="application/json",
        **headers,
    )
    body = _json_response(response)
    passed = response.status_code == expected_status and body.get("success") is True
    return {
        "legacy_route": legacy_name,
        "django_route": url,
        "status_code": response.status_code,
        "expected_status": expected_status,
        "passed": passed,
    }


def validate_security(client):
    """Validate permission and validation behavior for exposed write routes."""
    product_without_token = client.post(
        "/api/v1/catalog/products/",
        data={"name": "No token"},
        content_type="application/json",
    )
    bad_contact = client.post(
        "/api/v1/crm/contact-requests/",
        data={"message": "missing name"},
        content_type="application/json",
    )
    return [
        {
            "check": "product write requires admin token",
            "passed": product_without_token.status_code == 400
            and _json_response(product_without_token).get("error", {}).get("code") == "permission_denied",
        },
        {
            "check": "contact write validates required fields",
            "passed": bad_contact.status_code == 400
            and _json_response(bad_contact).get("error", {}).get("code") == "validation_error",
        },
    ]


def run_validation():
    """Run all Phase 11.1.1 replacement validations."""
    started_at = time.perf_counter()
    client = Client()
    get_results = [validate_get(client, legacy_name, url) for legacy_name, url in GET_REPLACEMENTS]
    write_results = [
        validate_write(client, legacy_name, method, url, payload, expected_status, headers)
        for legacy_name, method, url, payload, expected_status, headers in WRITE_REPLACEMENTS
    ]
    security_results = validate_security(client)
    all_results = get_results + write_results + security_results
    passed = all(result["passed"] for result in all_results)
    return {
        "status": "passed" if passed else "failed",
        "coverage": {
            "legacy_route_groups_total": 15,
            "documented_replacements": 15,
            "validated_runtime_groups": len(get_results) + len(write_results),
        },
        "get_replacements": get_results,
        "write_replacements": write_results,
        "security": security_results,
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
    }


def main():
    """CLI entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    result = run_validation()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
