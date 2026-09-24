from pathlib import Path
import re

import pytest
from django.test import Client

from apps.api.services.replacement_submission_service import list_submissions, reset_submissions
from apps.business_core.models import BusinessProduct


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def clear_submissions():
    """Keep in-memory public submissions isolated per test."""
    reset_submissions()
    yield
    reset_submissions()


def csrf_token_from(response):
    """Read CSRF token value from a rendered Django form."""
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode())
    assert match
    return match.group(1)


@pytest.mark.django_db
def test_public_homepage_renders_with_seo_metadata(client):
    BusinessProduct.objects.create(
        name="Homepage CNC Shaft",
        slug="homepage-cnc-shaft",
        status="published",
        short_description="Precision shaft for homepage.",
        category_name="Shaft",
        sort_order=-100,
    )

    response = client.get("/")

    assert response.status_code == 200
    assert b"MecPrecision VIETNAM" in response.content
    assert b'<meta name="description"' in response.content
    assert b"Homepage CNC Shaft" in response.content


@pytest.mark.django_db
def test_public_product_listing_and_category_filter(client):
    BusinessProduct.objects.create(
        name="Published Gear",
        slug="published-gear",
        status="published",
        category_name="Gear",
    )
    BusinessProduct.objects.create(
        name="Hidden Draft",
        slug="hidden-draft",
        status="draft",
        category_name="Draft",
    )

    all_response = client.get("/products")
    filter_response = client.get("/products", {"category": "Gear"})

    assert all_response.status_code == 200
    assert b"Published Gear" in all_response.content
    assert b"Hidden Draft" not in all_response.content
    assert filter_response.status_code == 200
    assert b"Published Gear" in filter_response.content


@pytest.mark.django_db
def test_public_product_detail_and_404(client):
    product = BusinessProduct.objects.create(
        name="Detail Fixture",
        slug="detail-fixture",
        status="published",
        description="Fixture detail page.",
        seo_title="Fixture SEO Title",
    )

    response = client.get(f"/product/{product.slug}")
    missing = client.get("/product/does-not-exist")

    assert response.status_code == 200
    assert b"Fixture SEO Title" in response.content
    assert b"Fixture detail page." in response.content
    assert missing.status_code == 404


def test_public_technology_page_renders(client):
    response = client.get("/technology")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Quy trình sản xuất" in content
    assert "Đo kiểm 3D CMM" in content


def test_public_news_page_renders(client):
    response = client.get("/news")

    assert response.status_code == 200
    assert "Tin Tức Công Nghệ" in response.content.decode()


@pytest.mark.django_db
def test_public_contact_submission_creates_safe_intent(client):
    response = client.post(
        "/contact",
        data={
            "form_name": "contact",
            "contact-name": "Wave 7 Contact",
            "contact-company": "Wave 7 Company",
            "contact-email": "wave7@example.com",
            "contact-message": "Need CNC support.",
            "contact-captcha_answer": "7",
        },
        follow=True,
    )
    submissions = list_submissions()

    assert response.status_code == 200
    assert len(submissions) == 1
    assert submissions[0]["submission_type"] == "contact_request"
    assert submissions[0]["payload"]["name"] == "Wave 7 Contact"


@pytest.mark.django_db
def test_public_quote_submission_creates_safe_intent(client):
    response = client.post(
        "/contact",
        data={
            "form_name": "quote",
            "quote-name": "Wave 7 Quote",
            "quote-email": "quote-wave7@example.com",
            "quote-product": "CNC shaft",
            "quote-quantity": "20",
            "quote-message": "Please quote this job.",
            "quote-captcha_answer": "7",
        },
        follow=True,
    )
    submissions = list_submissions()

    assert response.status_code == 200
    assert len(submissions) == 1
    assert submissions[0]["submission_type"] == "quote_request"
    assert submissions[0]["payload"]["product"] == "CNC shaft"


def test_public_contact_csrf_protection():
    csrf_client = Client(enforce_csrf_checks=True)
    response = csrf_client.post(
        "/contact",
        data={
            "form_name": "contact",
            "contact-name": "No CSRF",
            "contact-email": "csrf@example.com",
            "contact-captcha_answer": "7",
        },
    )

    assert response.status_code == 403


def test_public_contact_csrf_success_with_token():
    csrf_client = Client(enforce_csrf_checks=True)
    contact_page = csrf_client.get("/contact")
    token = csrf_token_from(contact_page)
    response = csrf_client.post(
        "/contact",
        data={
            "form_name": "contact",
            "contact-name": "CSRF OK",
            "contact-email": "csrf-ok@example.com",
            "contact-captcha_answer": "7",
            "csrfmiddlewaretoken": token,
        },
        follow=True,
    )

    assert response.status_code == 200
    assert len(list_submissions()) == 1


def test_wave7_public_runtime_uses_django_and_current_frontend():
    """The retired backend stays absent while current public assets remain."""
    assert not (PROJECT_ROOT / "backend").exists()
    assert (PROJECT_ROOT / "django_backend" / "apps" / "website" / "urls.py").exists()
    assert (PROJECT_ROOT / "figma_make_frontend" / "index.html").exists()
