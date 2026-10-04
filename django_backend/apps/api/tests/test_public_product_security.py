"""Phase 5B publication workflow and negative-exposure tests."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.business_core.models import BusinessProduct, PublicProductProjection
from apps.business_core.publication import PublicProductPublicationService
from apps.foundation.models import (
    FoundationAuthToken,
    FoundationPermission,
    FoundationRole,
    FoundationUser,
)
from apps.foundation.services import FoundationAuthService


def _auth(token):
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def _recursive_keys(value):
    if isinstance(value, dict):
        keys = set(value)
        for nested in value.values():
            keys.update(_recursive_keys(nested))
        return keys
    if isinstance(value, list):
        keys = set()
        for nested in value:
            keys.update(_recursive_keys(nested))
        return keys
    return set()


@pytest.fixture
def phase5b_data(db):
    role = FoundationRole.objects.create(name="Phase5B Publisher")
    role.permissions.add(
        *FoundationPermission.objects.filter(module="public_products")
    )
    user = FoundationUser.objects.create(
        email="phase5b-publisher@example.invalid",
        full_name="Phase 5B Publisher",
        password_hash="test-only",
        role=role,
    )
    raw_token = "phase5b-publication-token"
    FoundationAuthToken.objects.create(
        user=user,
        token_hash=FoundationAuthService.hash_token(raw_token),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    product = BusinessProduct.objects.create(
        name="Internal precision part",
        slug="internal-precision-part-phase5b",
        sku="SECRET-SKU-PHASE5B",
        price=Decimal("98765.43"),
        technical_requirements="SECRET-INTERNAL-NOTES-PHASE5B",
        is_active=True,
        created_by=user,
    )
    return {"token": raw_token, "user": user, "product": product}


def _projection_payload(product):
    return {
        "source_product_id": product.id,
        "title": "Approved precision component",
        "slug": "approved-precision-component-phase5b",
        "public_description": "Public description approved for website use.",
        "public_material": {"code": "SUS304", "name": "Stainless steel"},
        "public_specifications": [
            {"label": "Tolerance", "value": "±0.01 mm"}
        ],
        "category": "Precision machining",
        "main_image": "https://media.example.invalid/product.webp",
        "seo_title": "Approved precision component",
        "seo_description": "Approved SEO description.",
        "display_order": 10,
    }


@pytest.mark.django_db
def test_projection_create_and_update_do_not_mutate_business_product(phase5b_data):
    product = phase5b_data["product"]
    source_snapshot = {
        "name": product.name,
        "slug": product.slug,
        "price": product.price,
        "technical_requirements": product.technical_requirements,
    }
    fields = _projection_payload(product)
    fields.pop("source_product_id")
    service = PublicProductPublicationService()
    projection = service.create(source_product=product, actor=phase5b_data["user"], **fields)
    assert projection.publication_status == "DRAFT"

    updated = service.update(
        projection, actor=phase5b_data["user"], title="Updated public title"
    )
    assert updated.title == "Updated public title"
    product.refresh_from_db()
    assert {
        "name": product.name,
        "slug": product.slug,
        "price": product.price,
        "technical_requirements": product.technical_requirements,
    } == source_snapshot


@pytest.mark.django_db
def test_publication_state_machine_requires_review_and_approval(phase5b_data):
    product = phase5b_data["product"]
    fields = _projection_payload(product)
    fields.pop("source_product_id")
    service = PublicProductPublicationService()
    projection = service.create(source_product=product, actor=phase5b_data["user"], **fields)

    with pytest.raises(ValidationError):
        service.transition(projection, "PUBLISHED", actor=phase5b_data["user"])
    projection = service.transition(projection, "REVIEW", actor=phase5b_data["user"])
    projection = service.transition(projection, "APPROVED", actor=phase5b_data["user"])
    projection = service.transition(projection, "PUBLISHED", actor=phase5b_data["user"])
    assert projection.publication_status == "PUBLISHED"
    assert projection.published_at is not None

    with pytest.raises(ValidationError):
        service.update(
            projection,
            actor=phase5b_data["user"],
            title="Unsafe edit after publication",
        )


@pytest.mark.django_db
def test_admin_can_create_edit_and_transition_projection(client, phase5b_data):
    headers = _auth(phase5b_data["token"])
    created = client.post(
        "/api/v1/admin/public-products/",
        data=_projection_payload(phase5b_data["product"]),
        content_type="application/json",
        **headers,
    )
    assert created.status_code == 201, created.json()
    assert created.json()["data"]["publication_status"] == "DRAFT"
    projection = PublicProductProjection.objects.get()

    edited = client.put(
        f"/api/v1/admin/public-products/{projection.id}/",
        data={"public_description": "Updated and reviewed public copy."},
        content_type="application/json",
        **headers,
    )
    assert edited.status_code == 200, edited.json()
    for target in ("REVIEW", "APPROVED", "PUBLISHED"):
        transitioned = client.put(
            f"/api/v1/admin/public-products/{projection.id}/",
            data={"publication_status": target},
            content_type="application/json",
            **headers,
        )
        assert transitioned.status_code == 200, transitioned.json()
        assert transitioned.json()["data"]["publication_status"] == target


@pytest.mark.django_db
def test_draft_is_hidden_and_published_projection_is_public(client, phase5b_data):
    product = phase5b_data["product"]
    fields = _projection_payload(product)
    fields.pop("source_product_id")
    service = PublicProductPublicationService()
    projection = service.create(source_product=product, actor=phase5b_data["user"], **fields)

    draft_response = client.get("/api/v1/public/products/")
    assert draft_response.status_code == 200
    assert draft_response.json()["data"]["count"] == 0

    for target in ("REVIEW", "APPROVED", "PUBLISHED"):
        projection = service.transition(projection, target, actor=phase5b_data["user"])
    published_response = client.get("/api/v1/public/products/")
    assert published_response.status_code == 200
    data = published_response.json()["data"]
    assert data["count"] == 1
    assert data["results"][0]["slug"] == projection.slug


@pytest.mark.django_db
def test_public_product_response_has_no_sensitive_field_leakage(client, phase5b_data):
    product = phase5b_data["product"]
    fields = _projection_payload(product)
    fields.pop("source_product_id")
    service = PublicProductPublicationService()
    projection = service.create(source_product=product, actor=phase5b_data["user"], **fields)
    for target in ("REVIEW", "APPROVED", "PUBLISHED"):
        projection = service.transition(projection, target, actor=phase5b_data["user"])

    PublicProductProjection.objects.filter(pk=projection.pk).update(
        public_material={
            "code": "SUS304",
            "name": "Stainless steel",
            "internal_notes": "SECRET-NESTED-MATERIAL",
        },
        public_specifications=[
            {
                "label": "Tolerance",
                "value": "±0.01 mm",
                "cost": "SECRET-NESTED-COST",
            }
        ],
    )

    response = client.get("/api/v1/public/products/")
    assert response.status_code == 200
    payload = response.json()
    forbidden = {
        "source_product",
        "source_product_id",
        "legacy_product_id",
        "cost",
        "price",
        "quantity",
        "inventory",
        "customer_id",
        "order_id",
        "internal_notes",
        "technical_requirements",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
        "publication_status",
        "published_at",
    }
    assert _recursive_keys(payload).isdisjoint(forbidden)
    serialized = str(payload)
    assert "SECRET-SKU-PHASE5B" not in serialized
    assert "SECRET-INTERNAL-NOTES-PHASE5B" not in serialized
    assert "98765.43" not in serialized
    assert "SECRET-NESTED-MATERIAL" not in serialized
    assert "SECRET-NESTED-COST" not in serialized


@pytest.mark.django_db
def test_published_projection_is_hidden_when_source_becomes_inactive(client, phase5b_data):
    product = phase5b_data["product"]
    fields = _projection_payload(product)
    fields.pop("source_product_id")
    service = PublicProductPublicationService()
    projection = service.create(source_product=product, actor=phase5b_data["user"], **fields)
    for target in ("REVIEW", "APPROVED", "PUBLISHED"):
        projection = service.transition(projection, target, actor=phase5b_data["user"])
    product.is_active = False
    product.save(update_fields=["is_active"])

    response = client.get("/api/v1/public/products/")
    assert response.status_code == 200
    assert response.json()["data"]["count"] == 0


