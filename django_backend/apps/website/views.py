"""Django-owned public website views.

Wave 7 moves public page rendering into Django while keeping legacy files in
place for rollback. The views use Django services/models and avoid legacy
custom HTTP rendering.
"""

from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from apps.api.services.replacement_submission_service import create_submission
from apps.business_core.models import BusinessProduct
from apps.catalog.services.catalog_service import CatalogService
from apps.cms.services.cms_service import CmsService

from .forms import ContactForm, QuoteRequestForm


DEFAULT_HERO_IMAGE = (
    "https://images.unsplash.com/photo-1581092160607-ee22621dd758"
    "?auto=format&fit=crop&w=1400&q=80"
)


def _published_products():
    """Return products ready for public display."""
    return BusinessProduct.objects.filter(status="published").order_by("sort_order", "id")


def _featured_products(limit=6):
    """Return featured products with a draft fallback for demo data."""
    published = _published_products()[:limit]
    if published:
        return published
    return BusinessProduct.objects.all().order_by("sort_order", "id")[:limit]


def _categories_from_products():
    """Build a simple category list from Django-owned products."""
    categories = []
    seen = set()
    for name in BusinessProduct.objects.exclude(category_name="").values_list("category_name", flat=True):
        if name and name not in seen:
            categories.append(name)
            seen.add(name)
    return categories


def _safe_capabilities(limit=6):
    """Read capability content through the catalog service with a static fallback."""
    try:
        capabilities = list(CatalogService().list_capabilities()[:limit])
    except Exception:  # noqa: BLE001 - public pages should still render during legacy DB review.
        capabilities = []
    if capabilities:
        return capabilities
    return [
        {"title": "CNC machining", "content": "Precision turning, milling, and fixture manufacturing."},
        {"title": "Quality control", "content": "Dimensional inspection and process traceability."},
        {"title": "Engineering support", "content": "Manufacturing advice for drawings and prototypes."},
    ]


def _safe_news(limit=6):
    """Read news-like CMS pages through the CMS service with an empty fallback."""
    try:
        return list(CmsService().list_public_news()[:limit])
    except Exception:  # noqa: BLE001 - keep public site available if legacy read DB is unavailable.
        return []


def _seo(title, description, canonical_path="/"):
    """Build common SEO metadata for templates."""
    return {
        "title": title,
        "description": description,
        "canonical_path": canonical_path,
    }


def _form_payload(cleaned_data):
    """Convert form data to a plain payload for submission storage."""
    return {key: str(value or "").strip() for key, value in cleaned_data.items()}


def home(request):
    """Render the Django-owned homepage."""
    products = _featured_products()
    hero_product = products[0] if products else None
    return render(
        request,
        "website/home.html",
        {
            "seo": _seo(
                "MecPrecision VIETNAM - CNC precision machining",
                "Precision CNC machining, fixtures, and manufacturing support for industrial customers.",
            ),
            "hero_image": hero_product.main_image if hero_product and hero_product.main_image else DEFAULT_HERO_IMAGE,
            "featured_products": products,
            "capabilities": _safe_capabilities(4),
            "news_items": _safe_news(3),
        },
    )


def products(request):
    """Render product listing with category filtering."""
    category = (request.GET.get("category") or "").strip()
    queryset = _published_products()
    if not queryset.exists():
        queryset = BusinessProduct.objects.all().order_by("sort_order", "id")
    if category:
        queryset = queryset.filter(category_name=category)
    return render(
        request,
        "website/products.html",
        {
            "seo": _seo(
                "Products - MecPrecision VIETNAM",
                "Browse CNC machined shafts, gears, fixtures, and precision components.",
                "/products",
            ),
            "products": queryset,
            "categories": _categories_from_products(),
            "active_category": category,
        },
    )


def product_detail(request, slug):
    """Render one product detail page by slug."""
    try:
        product = BusinessProduct.objects.get(slug=slug)
    except BusinessProduct.DoesNotExist as exc:
        raise Http404("Product not found") from exc
    related = BusinessProduct.objects.exclude(id=product.id).order_by("sort_order", "id")[:3]
    return render(
        request,
        "website/product_detail.html",
        {
            "seo": _seo(
                product.seo_title or f"{product.name} - MecPrecision VIETNAM",
                product.seo_description or product.short_description or "Precision machined product.",
                f"/product/{product.slug}",
            ),
            "product": product,
            "related_products": related,
        },
    )


def technology(request):
    """Render the technology and manufacturing capability page."""
    return render(
        request,
        "website/technology.html",
        {
            "seo": _seo(
                "Technology - MecPrecision VIETNAM",
                "CNC manufacturing process, inspection capability, and engineering workflow.",
                "/technology",
            ),
            "capabilities": _safe_capabilities(8),
        },
    )


def news(request):
    """Render public news listing."""
    return render(
        request,
        "website/news.html",
        {
            "seo": _seo(
                "News - MecPrecision VIETNAM",
                "Manufacturing news, company updates, and technical notes.",
                "/news",
            ),
            "news_items": _safe_news(20),
        },
    )


def news_detail(request, slug):
    """Render one CMS-backed news/detail page."""
    try:
        page = CmsService().get_public_page(slug)
    except Exception as exc:  # noqa: BLE001 - normalize repository not-found variations.
        raise Http404("News item not found") from exc
    return render(
        request,
        "website/news_detail.html",
        {
            "seo": _seo(
                page.seo_title or page.title,
                page.seo_description or "MecPrecision public content.",
                f"/news/{page.slug}",
            ),
            "page": page,
        },
    )


def contact(request):
    """Render contact and quote forms, storing submissions through Django."""
    contact_form = ContactForm(prefix="contact")
    quote_form = QuoteRequestForm(prefix="quote")

    if request.method == "POST":
        form_name = request.POST.get("form_name", "")
        if form_name == "contact":
            contact_form = ContactForm(request.POST, prefix="contact")
            if contact_form.is_valid():
                create_submission("contact_request", "/contact", "POST", _form_payload(contact_form.cleaned_data))
                messages.success(request, "Your contact request was accepted.")
                return redirect("website:contact")
            messages.error(request, "Please check the contact form.")
        if form_name == "quote":
            quote_form = QuoteRequestForm(request.POST, prefix="quote")
            if quote_form.is_valid():
                create_submission("quote_request", "/contact", "POST", _form_payload(quote_form.cleaned_data))
                messages.success(request, "Your quote request was accepted.")
                return redirect("website:contact")
            messages.error(request, "Please check the quote form.")

    return render(
        request,
        "website/contact.html",
        {
            "seo": _seo(
                "Contact - MecPrecision VIETNAM",
                "Contact MecPrecision for CNC machining, fixtures, and quotation requests.",
                "/contact",
            ),
            "contact_form": contact_form,
            "quote_form": quote_form,
        },
    )


@require_GET
def api_home(request):
    """API endpoint matching frontend/js/app.js expectations (/api/home)."""
    products_qs = _featured_products()
    products_data = []
    for p in products_qs:
        products_data.append({
            "name": getattr(p, "name", ""),
            "category": getattr(p, "category_name", "") or "Chi tiết cơ khí",
            "image": getattr(p, "main_image", "") or DEFAULT_HERO_IMAGE,
            "description": getattr(p, "short_description", "") or getattr(p, "description", "") or "",
        })

    capabilities_raw = _safe_capabilities(4)
    capabilities_data = []
    for item in capabilities_raw:
        if isinstance(item, dict):
            capabilities_data.append({
                "icon": item.get("icon", ""),
                "title": item.get("title", ""),
                "text": item.get("content", item.get("text", "")),
            })
        else:
            capabilities_data.append({
                "icon": getattr(item, "icon", ""),
                "title": getattr(item, "title", ""),
                "text": getattr(item, "content", getattr(item, "description", "")),
            })

    news_raw = _safe_news(3)
    news_data = []
    for item in news_raw:
        if isinstance(item, dict):
            news_data.append({
                "title": item.get("title", ""),
                "category": item.get("category", "Tin tức"),
                "image": item.get("image", DEFAULT_HERO_IMAGE),
                "description": item.get("description", item.get("summary", "")),
            })
        else:
            news_data.append({
                "title": getattr(item, "title", ""),
                "category": getattr(item, "category", "Tin tức"),
                "image": getattr(item, "image", DEFAULT_HERO_IMAGE),
                "description": getattr(item, "summary", getattr(item, "description", "")),
            })

    return JsonResponse({
        "products": products_data,
        "capabilities": capabilities_data,
        "news": news_data,
    })

