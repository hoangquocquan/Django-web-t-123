"""Capability CMS workflow, exact permission, audit and public exposure tests."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.business_core.capabilities import CapabilityPublicationService
from apps.business_core.models import Capability
from apps.foundation.models import FoundationAuthToken, FoundationRole, FoundationUser
from apps.foundation.services import FoundationAuthService
from apps.transaction_domain.models import AuditEvent


def _headers(token):
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def _actor(role_name, suffix):
    user = FoundationUser.objects.create(
        email=f"capability-{suffix}@example.invalid",
        full_name=f"Capability {suffix}",
        password_hash="test-only",
        role=FoundationRole.objects.get(name=role_name),
    )
    token = f"capability-token-{suffix}"
    FoundationAuthToken.objects.create(
        user=user,
        token_hash=FoundationAuthService.hash_token(token),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    return user, token


@pytest.fixture
def capability_context(db):
    return {
        "editor": _actor("editor", "editor"),
        "manager": _actor("Manager", "manager"),
        "admin": _actor("Admin", "admin"),
        "viewer": _actor("viewer", "viewer"),
        "sales": _actor("Sales", "sales"),
        "wildcard": _actor("admin", "wildcard"),
    }


def _payload(**overrides):
    payload = {
        "title": "Five-axis machining",
        "slug": "five-axis-machining",
        "short_description": "Approved short public summary.",
        "description": "Reviewed public capability description.",
        "image": "https://media.example.invalid/capability.webp",
        "technology_type": "CNC",
        "process_category": "Machining",
        "display_order": 10,
        "is_active": True,
        "seo_title": "Five-axis machining",
        "seo_description": "Approved search description.",
    }
    payload.update(overrides)
    return payload


def _patch(client, capability, token, data):
    return client.patch(
        f"/api/v1/admin/capabilities/{capability.pk}/",
        data=data,
        content_type="application/json",
        **_headers(token),
    )


@pytest.mark.django_db
def test_capability_permission_mapping_is_exact():
    expected = {
        "editor": {"capabilities:read", "capabilities:edit"},
        "Manager": {
            "capabilities:read",
            "capabilities:review",
            "capabilities:approve",
        },
        "Admin": {
            "capabilities:read",
            "capabilities:publish",
            "capabilities:archive",
        },
        "viewer": {"capabilities:read"},
        "Sales": set(),
        "admin": set(),
    }
    for role_name, codes in expected.items():
        assert set(
            FoundationRole.objects.get(name=role_name)
            .permissions.filter(module="capabilities")
            .values_list("code", flat=True)
        ) == codes


@pytest.mark.django_db
def test_editor_create_edit_submit_and_manager_approve(client, capability_context):
    editor_token = capability_context["editor"][1]
    created = client.post(
        "/api/v1/admin/capabilities/",
        data=_payload(),
        content_type="application/json",
        **_headers(editor_token),
    )
    assert created.status_code == 201, created.json()
    capability = Capability.objects.get()
    assert capability.status == "DRAFT"
    edited = _patch(client, capability, editor_token, {"title": "Edited title"})
    assert edited.status_code == 200, edited.json()
    submitted = _patch(client, capability, editor_token, {"status": "REVIEW"})
    assert submitted.status_code == 200, submitted.json()

    manager_token = capability_context["manager"][1]
    approved = _patch(client, capability, manager_token, {"status": "APPROVED"})
    assert approved.status_code == 200, approved.json()
    denied = _patch(client, capability, manager_token, {"status": "PUBLISHED"})
    assert denied.status_code == 403
    capability.refresh_from_db()
    assert capability.status == "APPROVED"


@pytest.mark.django_db
def test_admin_publish_archive_and_audit(client, capability_context):
    service = CapabilityPublicationService()
    capability = service.create(actor=capability_context["editor"][0], **_payload())
    capability = service.transition(
        capability, "REVIEW", actor=capability_context["editor"][0]
    )
    capability = service.transition(
        capability, "APPROVED", actor=capability_context["manager"][0]
    )
    admin_token = capability_context["admin"][1]
    published = _patch(client, capability, admin_token, {"status": "PUBLISHED"})
    assert published.status_code == 200, published.json()
    archived = _patch(client, capability, admin_token, {"status": "ARCHIVED"})
    assert archived.status_code == 200, archived.json()
    assert AuditEvent.objects.filter(
        entity_type="capability",
        entity_id=str(capability.pk),
        action="capability.published",
        actor_user=capability_context["admin"][0],
        old_status="APPROVED",
        new_status="PUBLISHED",
    ).exists()
    assert AuditEvent.objects.filter(
        entity_type="capability", action="capability.archived"
    ).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("actor_name", ["viewer", "sales", "wildcard"])
def test_unauthorized_roles_cannot_edit_or_transition(
    client, capability_context, actor_name
):
    capability = CapabilityPublicationService().create(
        actor=capability_context["editor"][0], **_payload()
    )
    before_audits = AuditEvent.objects.count()
    response = _patch(
        client,
        capability,
        capability_context[actor_name][1],
        {"status": "REVIEW"},
    )
    assert response.status_code == 403
    capability.refresh_from_db()
    assert capability.status == "DRAFT"
    assert AuditEvent.objects.count() == before_audits


@pytest.mark.django_db
def test_public_api_hides_unpublished_and_allowlists_published(
    client, capability_context
):
    service = CapabilityPublicationService()
    capability = service.create(actor=capability_context["editor"][0], **_payload())
    assert client.get("/api/v1/public/capabilities/").json()["data"]["count"] == 0
    capability = service.transition(
        capability, "REVIEW", actor=capability_context["editor"][0]
    )
    capability = service.transition(
        capability, "APPROVED", actor=capability_context["manager"][0]
    )
    capability = service.transition(
        capability, "PUBLISHED", actor=capability_context["admin"][0]
    )
    response = client.get("/api/v1/public/capabilities/")
    assert response.status_code == 200
    result = response.json()["data"]["results"][0]
    assert set(result) == {
        "id",
        "slug",
        "title",
        "description",
        "image",
        "technology_type",
        "process_category",
    }
    assert result["slug"] == capability.slug
    forbidden = {"status", "published_at", "seo_title", "is_active", "permissions"}
    assert forbidden.isdisjoint(result)


@pytest.mark.django_db
def test_inactive_published_capability_is_not_public(client, capability_context):
    service = CapabilityPublicationService()
    capability = service.create(actor=capability_context["editor"][0], **_payload())
    for target, actor in (
        ("REVIEW", capability_context["editor"][0]),
        ("APPROVED", capability_context["manager"][0]),
        ("PUBLISHED", capability_context["admin"][0]),
    ):
        capability = service.transition(capability, target, actor=actor)
    Capability.objects.filter(pk=capability.pk).update(is_active=False)
    assert client.get("/api/v1/public/capabilities/").json()["data"]["count"] == 0


@pytest.mark.django_db
def test_audit_failure_rolls_back_capability_transition(
    capability_context, monkeypatch
):
    service = CapabilityPublicationService()
    capability = service.create(actor=capability_context["editor"][0], **_payload())

    def fail_audit(**_kwargs):
        raise RuntimeError("forced capability audit failure")

    monkeypatch.setattr("apps.business_core.capabilities._audit", fail_audit)
    with pytest.raises(RuntimeError, match="forced capability audit failure"):
        service.transition(
            capability, "REVIEW", actor=capability_context["editor"][0]
        )
    capability.refresh_from_db()
    assert capability.status == "DRAFT"


@pytest.mark.django_db
def test_unauthenticated_admin_api_is_denied(client):
    assert client.get("/api/v1/admin/capabilities/").status_code == 403
    assert client.post(
        "/api/v1/admin/capabilities/",
        data=_payload(),
        content_type="application/json",
    ).status_code == 403


