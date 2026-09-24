"""Django API replacements for legacy endpoints still pending decommission."""

from __future__ import annotations

import os

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from apps.api.serializers.catalog import category_to_dict, product_to_dict
from apps.api.serializers.cms import banner_to_dict, page_to_dict
from apps.api.services.replacement_submission_service import create_submission
from apps.api.views.helpers import bad_request, created, ok, paginated_ok
from apps.catalog.services.catalog_service import CatalogService
from apps.cms.services.cms_service import CmsService
from apps.core.api_compatibility import LEGACY_API_VERSION


VALID_PRODUCT_STATUSES = {"draft", "published", "archived"}


def _text(payload, key, default=""):
    """Normalize one text field from a request payload."""
    return str(payload.get(key, default) or "").strip()


def _require_fields(payload, fields):
    """Return a 400 response when required fields are missing."""
    missing = [field for field in fields if not _text(payload, field)]
    if missing:
        return bad_request(
            "validation_error",
            f"Missing required field(s): {', '.join(missing)}.",
        )
    return None


def _require_admin_token(request):
    """Protect product write replacements with a simple migration admin token."""
    expected = os.getenv("PHASE11_1_1_API_ADMIN_TOKEN", "dev-admin-token")
    provided = request.headers.get("X-Admin-Token", "")
    if provided != expected:
        return bad_request("permission_denied", "Valid X-Admin-Token is required.")
    return None


def capability_to_dict(capability):
    """Convert one manufacturing capability into JSON."""
    return {
        "id": capability.id,
        "title": capability.title,
        "content": capability.content,
        "icon_label": capability.icon_label,
        "sort_order": capability.sort_order,
        "created_at": capability.created_at,
    }


def news_to_dict(page):
    """Represent news replacement data using existing published CMS pages."""
    data = page_to_dict(page)
    data["source"] = "cms_pages"
    return data


@api_view(["GET"])
@permission_classes([AllowAny])
def home(request):
    """Replace legacy GET /api/home with a Django aggregate endpoint."""
    catalog_service = CatalogService()
    cms_service = CmsService()
    products = [product_to_dict(product) for product in catalog_service.list_products()[:6]]
    categories = [category_to_dict(category) for category in catalog_service.list_categories()[:6]]
    banners = [banner_to_dict(banner) for banner in cms_service.list_active_banners("home_slider")[:5]]
    return ok(
        {
            "hero": {
                "title": "MecPrecision VIETNAM",
                "description": "Gia công cơ khí chính xác, CNC, đồ gá và giải pháp sản xuất.",
            },
            "featured_products": products,
            "categories": categories,
            "banners": banners,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def capabilities(request):
    """Replace legacy GET /api/capabilities."""
    queryset = CatalogService().list_capabilities()
    return paginated_ok(request, queryset, capability_to_dict)


@api_view(["GET"])
@permission_classes([AllowAny])
def news(request):
    """Replace legacy GET /api/news with current CMS-backed public content."""
    queryset = CmsService().list_public_news()
    return paginated_ok(request, queryset, news_to_dict)


@api_view(["GET"])
@permission_classes([AllowAny])
def version(request):
    """Replace legacy GET /api/version."""
    return ok(
        {
            "version": LEGACY_API_VERSION,
            "api_namespace": "/api/v1",
            "replacement_phase": "11.1.1",
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def openapi_schema(request):
    """Replace legacy GET /api/openapi.json with a compact Django schema."""
    return ok(
        {
            "openapi": "3.0.3",
            "info": {
                "title": "MecPrecision Django API",
                "version": LEGACY_API_VERSION,
            },
            "servers": [{"url": "/api/v1"}],
            "paths": {
                "/public/home/": {"get": {"summary": "Home aggregate"}},
                "/catalog/products/": {"get": {"summary": "List products"}, "post": {"summary": "Create product intent"}},
                "/catalog/products/{id}/": {"get": {"summary": "Product detail"}, "put": {"summary": "Update product intent"}, "delete": {"summary": "Delete product intent"}},
                "/catalog/capabilities/": {"get": {"summary": "List capabilities"}},
                "/news/": {"get": {"summary": "List public news"}},
                "/crm/contact-requests/": {"get": {"summary": "List contact requests"}, "post": {"summary": "Create contact request intent"}},
                "/sales/quotes/": {"get": {"summary": "List quotes"}, "post": {"summary": "Create quote request intent"}},
                "/ai/chat/": {"post": {"summary": "AI chat replacement"}},
            },
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def aws_demo(request):
    """Replace legacy GET /api/aws-demo without calling AWS."""
    return ok(
        {
            "message": "Django API replacement is running.",
            "flow": ["browser", "django api", "service layer", "response json"],
            "aws_ready": {
                "compute": "EC2/ECS/Elastic Beanstalk",
                "database": "RDS PostgreSQL",
                "static_files": "S3 + CloudFront",
            },
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def external_weather(request):
    """Replace legacy weather demo with deterministic local demo data."""
    return ok(
        {
            "external_api": "Open-Meteo Forecast API",
            "mode": "local_demo",
            "message": "Django replacement endpoint is available; live network call is disabled in migration tests.",
            "forecast": {
                "city": request.query_params.get("city", "Ho Chi Minh City"),
                "temperature_c": 30,
                "condition": "demo",
            },
        }
    )


def contact_create(request):
    """Replace legacy POST /api/contact with validated Django write intent."""
    payload = request.data
    required_error = _require_fields(payload, ["name"])
    if required_error:
        return required_error
    if not (_text(payload, "contact") or _text(payload, "email") or _text(payload, "phone")):
        return bad_request("validation_error", "Contact, email or phone is required.")
    if _text(payload, "captcha_answer") and _text(payload, "captcha_answer") != "7":
        return bad_request("validation_error", "Captcha answer is not valid.")

    submission = create_submission("contact_request", "/api/contact", "POST", payload)
    return created(
        {
            "message": "Contact request accepted by Django API replacement.",
            "submission": submission,
        }
    )


def quote_create(request):
    """Replace legacy POST /api/quote-request with validated Django write intent."""
    payload = request.data
    required_error = _require_fields(payload, ["name"])
    if required_error:
        return required_error
    if not (_text(payload, "contact") or _text(payload, "email") or _text(payload, "phone")):
        return bad_request("validation_error", "Contact, email or phone is required.")
    if not (_text(payload, "product") or _text(payload, "project_name") or _text(payload, "message")):
        return bad_request("validation_error", "Product, project_name or message is required.")

    submission = create_submission("quote_request", "/api/quote-request", "POST", payload)
    return created(
        {
            "message": "Quote request accepted by Django API replacement.",
            "submission": submission,
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def ai_chat(request):
    """Replace legacy POST /api/ai/chat with a deterministic migration-safe reply."""
    question = _text(request.data, "question") or _text(request.data, "message")
    if not question:
        return bad_request("validation_error", "Question is required.")
    return ok(
        {
            "answer": "Django AI replacement endpoint is available. Ollama integration remains a later runtime concern.",
            "question": question,
            "model": "migration-safe-demo",
        }
    )


def product_create(request):
    """Replace legacy POST /api/products with an admin-protected write intent."""
    token_error = _require_admin_token(request)
    if token_error:
        return token_error
    required_error = _require_fields(
        request.data,
        ["category_id", "name", "short_description", "description", "main_image"],
    )
    if required_error:
        return required_error
    status = _text(request.data, "status", "published") or "published"
    if status not in VALID_PRODUCT_STATUSES:
        return bad_request("validation_error", "Status must be draft, published or archived.")

    submission = create_submission("product", "/api/products", "POST", request.data)
    return created(
        {
            "message": "Product create intent accepted by Django API replacement.",
            "submission": submission,
        }
    )


def product_write_detail(request, product_id):
    """Replace legacy PUT/DELETE /api/products/{id} with protected write intents."""
    token_error = _require_admin_token(request)
    if token_error:
        return token_error
    operation = request.method
    payload = dict(request.data or {})
    payload["product_id"] = product_id
    submission = create_submission("product", f"/api/products/{product_id}", operation, payload)
    return ok(
        {
            "message": f"Product {operation.lower()} intent accepted by Django API replacement.",
            "submission": submission,
        }
    )
