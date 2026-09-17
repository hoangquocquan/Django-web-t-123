"""Focused Phase 6A legacy write-boundary regression tests."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.business_core.models import BusinessCustomer, BusinessMaterial, BusinessProduct
from apps.foundation.models import FoundationAuthToken, FoundationPermission, FoundationRole, FoundationUser
from apps.foundation.services import FoundationAuthService
from apps.transaction_domain.models import AuditEvent


def _permission(module, action):
    permission, _created = FoundationPermission.objects.get_or_create(
        module=module,
        action=action,
        defaults={"code": f"phase6:{module}:{action}"},
    )
    return permission


def _actor(name, permissions=(), *, user_active=True, role_active=True, canonical_role=None):
    role, _created = FoundationRole.objects.get_or_create(
        name=canonical_role or f"Phase6-{name}",
        defaults={"is_active": role_active},
    )
    role.is_active = role_active
    role.save(update_fields=["is_active"])
    role.permissions.add(*[_permission(module, action) for module, action in permissions])
    user = FoundationUser.objects.create(
        email=f"{name}@phase6.invalid",
        full_name=name,
        password_hash="test-only",
        role=role,
        is_active=user_active,
    )
    raw = f"phase6-{name}-token"
    FoundationAuthToken.objects.create(
        user=user,
        token_hash=FoundationAuthService.hash_token(raw),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    return user, raw


@pytest.fixture
def phase6_boundary(db):
    writer, writer_token = _actor(
        "writer",
        (("customers", "write"), ("products", "write"), ("customer", "view"), ("customer", "change")),
        canonical_role="Sales",
    )
    _inactive, inactive_token = _actor(
        "inactive", (("customers", "write"),), user_active=False
    )
    _inactive_role, inactive_role_token = _actor(
        "inactive-role", (("customers", "write"),), role_active=False
    )
    _wildcard, wildcard_token = _actor("wildcard", (("*", "*"),))
    _wrong, wrong_token = _actor("wrong-role", (("orders", "read"),))
    customer = BusinessCustomer.objects.create(
        data_contract="MVP_V1",
        customer_code="CUS-P6-BOUNDARY",
        company_name="Canonical customer",
        contact_name="Fictional buyer",
        email="buyer@phase6.invalid",
        status="ACTIVE",
        created_by=writer,
        updated_by=writer,
    )
    material = BusinessMaterial.objects.create(
        data_contract="MVP_V1",
        material_code="MAT-P6-BOUNDARY",
        name="Test steel",
        created_by=writer,
    )
    product = BusinessProduct.objects.create(
        data_contract="MVP_V1",
        part_code="PART-P6-BOUNDARY",
        revision="A",
        unit="PCS",
        name="Canonical part",
        slug="canonical-part-p6-boundary",
        default_material=material,
        created_by=writer,
    )
    return {
        "writer": writer,
        "tokens": {
            "writer": writer_token,
            "inactive": inactive_token,
            "inactive_role": inactive_role_token,
            "wildcard": wildcard_token,
            "wrong": wrong_token,
        },
        "customer": customer,
        "product": product,
    }


def _auth(token):
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.mark.django_db
@pytest.mark.parametrize("actor", [None, "inactive", "inactive_role", "wildcard", "wrong", "writer"])
def test_legacy_customer_update_denials_are_atomic(client, phase6_boundary, actor):
    customer = phase6_boundary["customer"]
    before_audits = AuditEvent.objects.count()
    headers = {} if actor is None else _auth(phase6_boundary["tokens"][actor])
    response = client.put(
        f"/api/v1/business/customers/{customer.pk}/",
        {"company_name": "Forbidden mutation"},
        content_type="application/json",
        **headers,
    )
    assert response.status_code in {400, 403}
    customer.refresh_from_db()
    assert customer.company_name == "Canonical customer"
    assert AuditEvent.objects.count() == before_audits


@pytest.mark.django_db
def test_admin_alias_cannot_update_mvp_product(client, phase6_boundary):
    product = phase6_boundary["product"]
    before_audits = AuditEvent.objects.count()
    response = client.put(
        f"/api/v1/admin/products/{product.pk}/",
        {"name": "Forbidden mutation"},
        content_type="application/json",
        **_auth(phase6_boundary["tokens"]["writer"]),
    )
    assert response.status_code == 400
    product.refresh_from_db()
    assert product.name == "Canonical part"
    assert AuditEvent.objects.count() == before_audits


@pytest.mark.django_db
def test_legacy_record_update_remains_permitted(client, phase6_boundary):
    legacy = BusinessCustomer.objects.create(
        data_contract="LEGACY",
        company_name="Legacy customer",
        contact_name="Legacy contact",
        email="legacy@phase6.invalid",
        status="active",
    )
    response = client.put(
        f"/api/v1/business/customers/{legacy.pk}/",
        {"company_name": "Updated legacy customer"},
        content_type="application/json",
        **_auth(phase6_boundary["tokens"]["writer"]),
    )
    assert response.status_code == 200, response.json()
    legacy.refresh_from_db()
    assert legacy.company_name == "Updated legacy customer"


@pytest.mark.django_db
def test_canonical_customer_command_is_preserved(client, phase6_boundary):
    customer = phase6_boundary["customer"]
    response = client.post(
        f"/api/v1/canonical/customers/{customer.pk}/commands/update/",
        {"company_name": "Canonical update"},
        content_type="application/json",
        **_auth(phase6_boundary["tokens"]["writer"]),
    )
    assert response.status_code == 200, response.json()
    customer.refresh_from_db()
    assert customer.company_name == "Canonical update"
    assert AuditEvent.objects.filter(action="customer.updated", entity_id=str(customer.pk)).count() == 1
