"""Phase 5C exact Public Product RBAC, transition and audit tests."""

from datetime import timedelta

import pytest
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
from apps.transaction_domain.models import AuditEvent


def _headers(token):
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def _user_with_token(role_name, suffix):
    role = FoundationRole.objects.get(name=role_name)
    user = FoundationUser.objects.create(
        email=f"phase5c-{suffix}@example.invalid",
        full_name=f"Phase 5C {suffix}",
        password_hash="test-only",
        role=role,
    )
    token = f"phase5c-token-{suffix}"
    FoundationAuthToken.objects.create(
        user=user,
        token_hash=FoundationAuthService.hash_token(token),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    return user, token


@pytest.fixture
def phase5c_context(db):
    actors = {
        "editor": _user_with_token("editor", "editor"),
        "manager": _user_with_token("Manager", "manager"),
        "publisher": _user_with_token("Admin", "publisher"),
        "viewer": _user_with_token("viewer", "viewer"),
        "sales": _user_with_token("Sales", "sales"),
        "wildcard": _user_with_token("admin", "wildcard"),
    }
    product = BusinessProduct.objects.create(
        name="Phase 5C source product",
        slug="phase5c-source-product",
        is_active=True,
        created_by=actors["editor"][0],
    )
    return {"actors": actors, "product": product}


def _payload(product):
    return {
        "source_product_id": product.pk,
        "title": "Approved Phase 5C product",
        "slug": "approved-phase5c-product",
        "public_description": "Reviewed public description.",
        "public_material": {"code": "SUS304", "name": "Stainless steel"},
        "public_specifications": [{"label": "Tolerance", "value": "±0.01 mm"}],
        "category": "CNC",
        "main_image": "",
        "seo_title": "",
        "seo_description": "",
        "display_order": 0,
    }


def _put(client, projection, token, payload):
    return client.put(
        f"/api/v1/admin/public-products/{projection.pk}/",
        data=payload,
        content_type="application/json",
        **_headers(token),
    )


@pytest.mark.django_db
def test_phase5c_role_mapping_is_exact_and_sales_receives_none():
    expected = {
        "editor": {"public_products:read", "public_products:edit"},
        "Manager": {
            "public_products:read",
            "public_products:review",
            "public_products:approve",
        },
        "Admin": {
            "public_products:read",
            "public_products:publish",
            "public_products:archive",
        },
        "viewer": {"public_products:read"},
        "Sales": set(),
        "admin": set(),
    }
    for role_name, expected_codes in expected.items():
        actual = set(
            FoundationRole.objects.get(name=role_name)
            .permissions.filter(module="public_products")
            .values_list("code", flat=True)
        )
        assert actual == expected_codes
    assert FoundationPermission.objects.filter(module="public_products").count() == 6


@pytest.mark.django_db
def test_editor_edits_but_cannot_publish(client, phase5c_context):
    editor_token = phase5c_context["actors"]["editor"][1]
    created = client.post(
        "/api/v1/admin/public-products/",
        data=_payload(phase5c_context["product"]),
        content_type="application/json",
        **_headers(editor_token),
    )
    assert created.status_code == 201, created.json()
    projection = PublicProductProjection.objects.get()
    edited = _put(client, projection, editor_token, {"title": "Edited public title"})
    assert edited.status_code == 200, edited.json()
    submitted = _put(client, projection, editor_token, {"publication_status": "REVIEW"})
    assert submitted.status_code == 200, submitted.json()

    manager_token = phase5c_context["actors"]["manager"][1]
    approved = _put(client, projection, manager_token, {"publication_status": "APPROVED"})
    assert approved.status_code == 200, approved.json()
    denied = _put(client, projection, editor_token, {"publication_status": "PUBLISHED"})
    assert denied.status_code == 403
    projection.refresh_from_db()
    assert projection.publication_status == "APPROVED"


@pytest.mark.django_db
def test_reviewer_approves_but_cannot_publish(client, phase5c_context):
    editor_user, _editor_token = phase5c_context["actors"]["editor"]
    fields = _payload(phase5c_context["product"])
    fields.pop("source_product_id")
    service = PublicProductPublicationService()
    projection = service.create(
        source_product=phase5c_context["product"], actor=editor_user, **fields
    )
    projection = service.transition(projection, "REVIEW", actor=editor_user)
    manager_token = phase5c_context["actors"]["manager"][1]

    approved = _put(client, projection, manager_token, {"publication_status": "APPROVED"})
    assert approved.status_code == 200, approved.json()
    denied = _put(client, projection, manager_token, {"publication_status": "PUBLISHED"})
    assert denied.status_code == 403
    projection.refresh_from_db()
    assert projection.publication_status == "APPROVED"


@pytest.mark.django_db
def test_publisher_publishes_and_archives_with_audit(client, phase5c_context):
    editor_user = phase5c_context["actors"]["editor"][0]
    manager_user = phase5c_context["actors"]["manager"][0]
    fields = _payload(phase5c_context["product"])
    fields.pop("source_product_id")
    service = PublicProductPublicationService()
    projection = service.create(
        source_product=phase5c_context["product"], actor=editor_user, **fields
    )
    projection = service.transition(projection, "REVIEW", actor=editor_user)
    projection = service.transition(projection, "APPROVED", actor=manager_user)
    publisher_token = phase5c_context["actors"]["publisher"][1]

    published = _put(client, projection, publisher_token, {"publication_status": "PUBLISHED"})
    assert published.status_code == 200, published.json()
    projection.refresh_from_db()
    assert projection.publication_status == "PUBLISHED"
    event = AuditEvent.objects.get(
        entity_type="public_product", action="public_product.published"
    )
    assert event.actor_user == phase5c_context["actors"]["publisher"][0]
    assert (event.old_status, event.new_status) == ("APPROVED", "PUBLISHED")

    archived = _put(client, projection, publisher_token, {"publication_status": "ARCHIVED"})
    assert archived.status_code == 200, archived.json()
    projection.refresh_from_db()
    assert projection.publication_status == "ARCHIVED"
    assert AuditEvent.objects.filter(
        entity_type="public_product",
        entity_id=str(projection.public_id),
        action="public_product.archived",
        old_status="PUBLISHED",
        new_status="ARCHIVED",
    ).exists()


@pytest.mark.django_db
def test_viewer_reads_but_cannot_edit(client, phase5c_context):
    editor_user = phase5c_context["actors"]["editor"][0]
    fields = _payload(phase5c_context["product"])
    fields.pop("source_product_id")
    projection = PublicProductPublicationService().create(
        source_product=phase5c_context["product"], actor=editor_user, **fields
    )
    viewer_token = phase5c_context["actors"]["viewer"][1]
    read = client.get("/api/v1/admin/public-products/", **_headers(viewer_token))
    assert read.status_code == 200, read.json()
    denied = _put(client, projection, viewer_token, {"title": "Forbidden edit"})
    assert denied.status_code == 403
    projection.refresh_from_db()
    assert projection.title == "Approved Phase 5C product"


@pytest.mark.django_db
@pytest.mark.parametrize("actor_name", ["sales", "wildcard"])
def test_unauthorized_and_wildcard_users_cannot_transition(
    client, phase5c_context, actor_name
):
    editor_user = phase5c_context["actors"]["editor"][0]
    fields = _payload(phase5c_context["product"])
    fields.pop("source_product_id")
    projection = PublicProductPublicationService().create(
        source_product=phase5c_context["product"], actor=editor_user, **fields
    )
    before_audits = AuditEvent.objects.count()
    token = phase5c_context["actors"][actor_name][1]
    denied = _put(client, projection, token, {"publication_status": "REVIEW"})
    assert denied.status_code == 403
    projection.refresh_from_db()
    assert projection.publication_status == "DRAFT"
    assert AuditEvent.objects.count() == before_audits


@pytest.mark.django_db
def test_audit_failure_rolls_back_transition(phase5c_context, monkeypatch):
    editor_user = phase5c_context["actors"]["editor"][0]
    fields = _payload(phase5c_context["product"])
    fields.pop("source_product_id")
    service = PublicProductPublicationService()
    projection = service.create(
        source_product=phase5c_context["product"], actor=editor_user, **fields
    )

    def fail_audit(**_kwargs):
        raise RuntimeError("forced Phase 5C audit failure")

    monkeypatch.setattr("apps.business_core.publication._audit", fail_audit)
    with pytest.raises(RuntimeError, match="forced Phase 5C audit failure"):
        service.transition(projection, "REVIEW", actor=editor_user)
    projection.refresh_from_db()
    assert projection.publication_status == "DRAFT"


