"""Focused Phase 4C canonical quotation and conversion command tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.db import close_old_connections, connection
from django.utils import timezone

from apps.api.canonical_contract import CanonicalConflict
from apps.api.services import canonical_command_service as command_module
from apps.api.services.canonical_command_service import QuotationCommandService
from apps.business_core.models import BusinessCustomer, BusinessMaterial, BusinessProduct
from apps.foundation.models import (
    FoundationAuthToken,
    FoundationPermission,
    FoundationRole,
    FoundationUser,
)
from apps.foundation.services import FoundationAuthService
from apps.sales.models import (
    SalesQuotation,
    SalesQuotationApprovalDecision,
    SalesQuotationCustomerDecision,
    SalesRfq,
    SalesRfqLine,
)
from apps.transaction_domain.models import AuditEvent, TransactionOrder


ROLE_PERMISSIONS = {
    "Admin": {
        "quotation:view", "quotation:create_revision", "quotation:change",
        "quotation:archive", "quotation:submit", "quotation:send",
        "quotation:record_customer_decision", "quotation:convert", "order:view",
    },
    "Sales": {
        "quotation:view", "quotation:create_revision", "quotation:change",
        "quotation:archive", "quotation:submit", "quotation:send",
        "quotation:record_customer_decision", "quotation:convert", "order:view",
    },
    "Manager": {"quotation:view", "quotation:approve", "quotation:reject"},
}


def _permission(code):
    module, action = code.split(":", 1)
    permission, _created = FoundationPermission.objects.get_or_create(
        code=code,
        defaults={"module": module, "action": action, "description": "Phase 4C test"},
    )
    return permission


def _user(role_name, suffix, permissions=(), *, active=True):
    role, _created = FoundationRole.objects.get_or_create(name=role_name)
    role.is_active = True
    role.save(update_fields=["is_active"])
    for code in permissions:
        role.permissions.add(_permission(code))
    return FoundationUser.objects.create(
        email=f"{suffix}@phase4c.example",
        full_name=f"Phase 4C {suffix}",
        password_hash="test-only-placeholder",
        role=role,
        is_active=active,
    )


def _token(user, suffix):
    raw = f"phase4c-{suffix}-credential"
    FoundationAuthToken.objects.create(
        user=user,
        token_hash=FoundationAuthService.hash_token(raw),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    return raw


def _headers(context, actor):
    return {"HTTP_AUTHORIZATION": f"Bearer {context['tokens'][actor]}"}


@pytest.fixture
def phase4c_context(db):
    users = {
        role.casefold(): _user(role, role.casefold(), permissions)
        for role, permissions in ROLE_PERMISSIONS.items()
    }
    users["other_sales"] = _user("Sales", "other-sales", ROLE_PERMISSIONS["Sales"])
    users["inactive"] = _user(
        "Sales", "inactive", ROLE_PERMISSIONS["Sales"], active=False
    )
    users["unassigned"] = _user("Unassigned", "unassigned")
    users["wildcard"] = _user("Wildcard", "wildcard")
    users["wildcard"].role.permissions.add(_permission("*:*"))
    users["missing"] = _user("Sales", "missing", {"quotation:view"})
    tokens = {name: _token(user, name) for name, user in users.items()}

    customer = BusinessCustomer.objects.create(
        data_contract="MVP_V1",
        customer_code="CUS-P4C-001",
        company_name="Phase 4C Customer",
        contact_name="Buyer",
        email="buyer@example.invalid",
        status="ACTIVE",
        created_by=users["sales"],
        updated_by=users["sales"],
    )
    material = BusinessMaterial.objects.create(
        data_contract="MVP_V1",
        material_code="MAT-P4C-001",
        name="SUS304",
        standard="JIS",
        grade="304",
        created_by=users["admin"],
        updated_by=users["admin"],
    )
    part = BusinessProduct.objects.create(
        data_contract="MVP_V1",
        part_code="PART-P4C-001",
        name="Precision shaft",
        slug="phase4c-precision-shaft",
        revision="A",
        unit="PCS",
        default_material=material,
        tolerance="h6",
        technical_requirements="Turn and grind",
        created_by=users["admin"],
        updated_by=users["admin"],
    )
    today = timezone.localdate()
    rfq = SalesRfq.objects.create(
        data_contract="MVP_V1",
        rfq_number="RFQ-P4C-001",
        customer=customer,
        status="READY_TO_QUOTE",
        project_name="Canonical quotation",
        quote_due_at=today + timedelta(days=3),
        required_delivery_date=today + timedelta(days=30),
        assigned_to=users["sales"],
        created_by=users["sales"],
        updated_by=users["sales"],
    )
    line = SalesRfqLine.objects.create(
        rfq=rfq,
        line_number=1,
        part=part,
        material=material,
        description="Shaft per controlled drawing",
        quantity="2.5000",
        unit="PCS",
        required_delivery_date=today + timedelta(days=30),
        tolerance="h6",
        technical_notes="Surface finish Ra 0.8",
        drawing_required=False,
    )
    return {
        "users": users,
        "tokens": tokens,
        "customer": customer,
        "material": material,
        "part": part,
        "rfq": rfq,
        "line": line,
    }


def _quotation_payload(context, *, currency="USD", unit_price="9.385", terms="Net 30"):
    today = timezone.localdate()
    return {
        "currency": currency,
        "valid_from": today.isoformat(),
        "valid_until": (today + timedelta(days=14)).isoformat(),
        "discount_total": "1.01",
        "tax_amount": "2.35",
        "terms": terms,
        "lines": [
            {
                "source_rfq_line_id": context["line"].pk,
                "unit_price": unit_price,
                "discount": "0.51",
            }
        ],
    }


def _create_quotation(client, context, *, actor="sales", key="phase4c-create-1", **payload):
    body = _quotation_payload(context, **payload)
    response = client.post(
        f"/api/v1/canonical/rfqs/{context['rfq'].pk}/quotations/commands/create/",
        body,
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY=key,
        **_headers(context, actor),
    )
    assert response.status_code == 201, response.json()
    return SalesQuotation.objects.get(pk=response.json()["data"]["id"])


def _submit(client, context, quotation, *, actor="sales"):
    response = client.post(
        f"/api/v1/canonical/quotations/{quotation.pk}/commands/submit/",
        {},
        content_type="application/json",
        **_headers(context, actor),
    )
    assert response.status_code == 200, response.json()
    quotation.refresh_from_db()
    return quotation


def _approve(client, context, quotation):
    response = client.post(
        f"/api/v1/canonical/quotations/{quotation.pk}/commands/approve/",
        {"notes": "Commercial approval"},
        content_type="application/json",
        **_headers(context, "manager"),
    )
    assert response.status_code == 200, response.json()
    quotation.refresh_from_db()
    return quotation


def _send(client, context, quotation):
    response = client.post(
        f"/api/v1/canonical/quotations/{quotation.pk}/commands/send/",
        {"sent_to": "Buyer", "evidence": "CRM message P4C-001"},
        content_type="application/json",
        **_headers(context, "sales"),
    )
    assert response.status_code == 200, response.json()
    quotation.refresh_from_db()
    return quotation


def _accept(client, context, quotation):
    response = client.post(
        f"/api/v1/canonical/quotations/{quotation.pk}/commands/accept/",
        {"contact_snapshot": "Buyer", "evidence": "Signed acceptance P4C-001"},
        content_type="application/json",
        **_headers(context, "sales"),
    )
    assert response.status_code == 200, response.json()
    quotation.refresh_from_db()
    return quotation


@pytest.mark.django_db
def test_create_requires_auth_exact_permissions_and_active_user(client, phase4c_context):
    path = f"/api/v1/canonical/rfqs/{phase4c_context['rfq'].pk}/quotations/commands/create/"
    payload = _quotation_payload(phase4c_context)
    assert client.post(path, payload, content_type="application/json").status_code == 401
    for actor, expected in (
        ("inactive", 401),
        ("wildcard", 403),
        ("unassigned", 403),
        ("missing", 403),
        ("manager", 403),
    ):
        response = client.post(
            path,
            payload,
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY=f"denied-{actor}",
            **_headers(phase4c_context, actor),
        )
        assert response.status_code == expected


@pytest.mark.django_db
def test_inactive_role_is_denied_fail_closed(client, phase4c_context):
    role = phase4c_context["users"]["sales"].role
    role.is_active = False
    role.save(update_fields=["is_active"])
    response = client.post(
        f"/api/v1/canonical/rfqs/{phase4c_context['rfq'].pk}/quotations/commands/create/",
        _quotation_payload(phase4c_context),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="inactive-role",
        **_headers(phase4c_context, "sales"),
    )
    assert response.status_code == 403
    read_response = client.get(
        "/api/v1/canonical/quotations/",
        **_headers(phase4c_context, "sales"),
    )
    assert read_response.status_code == 403


@pytest.mark.django_db
def test_initial_creation_idempotency_money_and_protected_fields(client, phase4c_context):
    path = f"/api/v1/canonical/rfqs/{phase4c_context['rfq'].pk}/quotations/commands/create/"
    payload = _quotation_payload(phase4c_context)
    missing = client.post(
        path, payload, content_type="application/json", **_headers(phase4c_context, "sales")
    )
    assert missing.status_code == 400

    first = client.post(
        path,
        payload,
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="create-replay",
        **_headers(phase4c_context, "sales"),
    )
    assert first.status_code == 201
    replay = client.post(
        path,
        payload,
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="create-replay",
        **_headers(phase4c_context, "sales"),
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["id"] == first.json()["data"]["id"]
    assert SalesQuotation.objects.count() == 1
    assert AuditEvent.objects.filter(action="quotation.created").count() == 1

    quotation = SalesQuotation.objects.get()
    assert str(quotation.subtotal) == "23.4600"
    assert str(quotation.discount_total) == "1.0100"
    assert str(quotation.tax_amount) == "2.3500"
    assert str(quotation.total) == "24.8000"
    body = first.json()
    serialized = str(body).casefold()
    assert "idempotency" not in serialized and "request_hash" not in serialized
    assert "password" not in serialized and "token" not in serialized

    conflict_payload = {**payload, "terms": "Different"}
    conflict = client.post(
        path,
        conflict_payload,
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="create-replay",
        **_headers(phase4c_context, "sales"),
    )
    assert conflict.status_code == 409

    protected = client.post(
        path,
        {**payload, "total": "0", "revision": 99, "created_by_id": 1},
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="protected-fields",
        **_headers(phase4c_context, "sales"),
    )
    assert protected.status_code == 400


@pytest.mark.django_db
def test_creation_requires_ready_rfq_and_admin_is_allowed(client, phase4c_context):
    path = f"/api/v1/canonical/rfqs/{phase4c_context['rfq'].pk}/quotations/commands/create/"
    phase4c_context["rfq"].status = "DRAFT"
    phase4c_context["rfq"].save(update_fields=["status", "updated_at"])
    blocked = client.post(
        path,
        _quotation_payload(phase4c_context),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="wrong-rfq-state",
        **_headers(phase4c_context, "admin"),
    )
    assert blocked.status_code == 409
    phase4c_context["rfq"].status = "READY_TO_QUOTE"
    phase4c_context["rfq"].save(update_fields=["status", "updated_at"])
    created = client.post(
        path,
        _quotation_payload(phase4c_context),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="admin-create",
        **_headers(phase4c_context, "admin"),
    )
    assert created.status_code == 201


@pytest.mark.django_db
def test_draft_update_ownership_rounding_immutability_and_archive(client, phase4c_context):
    quotation = _create_quotation(client, phase4c_context)
    update_path = f"/api/v1/canonical/quotations/{quotation.pk}/commands/update/"
    denied = client.post(
        update_path,
        {"terms": "Not owner"},
        content_type="application/json",
        **_headers(phase4c_context, "other_sales"),
    )
    assert denied.status_code == 403
    floating = client.post(
        update_path,
        {"tax_amount": 1.25},
        content_type="application/json",
        **_headers(phase4c_context, "sales"),
    )
    assert floating.status_code == 400
    updated = client.post(
        update_path,
        {
            "terms": "Repriced",
            "lines": [{
                "source_rfq_line_id": phase4c_context["line"].pk,
                "unit_price": "10.005",
                "discount": "0.005",
            }],
            "discount_total": "0",
            "tax_amount": "0",
        },
        content_type="application/json",
        **_headers(phase4c_context, "sales"),
    )
    assert updated.status_code == 200, updated.json()
    quotation.refresh_from_db()
    line = quotation.lines.get()
    assert quotation.terms == "Repriced"
    assert str(line.line_subtotal) == "25.0100"
    assert str(line.discount) == "0.0100"
    assert str(line.line_total) == "25.0000"

    _submit(client, phase4c_context, quotation)
    immutable = client.post(
        update_path,
        {"terms": "Illegal mutation"},
        content_type="application/json",
        **_headers(phase4c_context, "sales"),
    )
    assert immutable.status_code == 409
    quotation.refresh_from_db()
    assert quotation.terms == "Repriced"


@pytest.mark.django_db
def test_archive_is_draft_only_preserves_revision_and_denies_manager(client, phase4c_context):
    quotation = _create_quotation(client, phase4c_context)
    path = f"/api/v1/canonical/quotations/{quotation.pk}/commands/archive/"
    denied = client.post(
        path, {}, content_type="application/json", **_headers(phase4c_context, "manager")
    )
    assert denied.status_code == 403
    archived = client.post(
        path, {}, content_type="application/json", **_headers(phase4c_context, "sales")
    )
    assert archived.status_code == 200
    quotation.refresh_from_db()
    assert quotation.workflow_status == "SUPERSEDED"
    assert SalesQuotation.objects.filter(pk=quotation.pk).exists()
    assert AuditEvent.objects.filter(
        action="quotation.superseded", entity_id=str(quotation.pk)
    ).count() == 1
    again = client.post(
        path, {}, content_type="application/json", **_headers(phase4c_context, "admin")
    )
    assert again.status_code == 409


@pytest.mark.django_db
def test_manager_only_decision_rejection_reason_maker_checker_and_revision(client, phase4c_context):
    quotation = _submit(
        client, phase4c_context, _create_quotation(client, phase4c_context)
    )
    approve_path = f"/api/v1/canonical/quotations/{quotation.pk}/commands/approve/"
    for actor in ("admin", "sales"):
        response = client.post(
            approve_path,
            {},
            content_type="application/json",
            **_headers(phase4c_context, actor),
        )
        assert response.status_code == 403

    SalesQuotation.objects.filter(pk=quotation.pk).update(
        created_by=phase4c_context["users"]["manager"]
    )
    maker_checker = client.post(
        approve_path,
        {},
        content_type="application/json",
        **_headers(phase4c_context, "manager"),
    )
    assert maker_checker.status_code == 400
    assert SalesQuotationApprovalDecision.objects.count() == 0
    SalesQuotation.objects.filter(pk=quotation.pk).update(
        created_by=phase4c_context["users"]["sales"]
    )

    reject_path = f"/api/v1/canonical/quotations/{quotation.pk}/commands/reject/"
    missing_reason = client.post(
        reject_path,
        {},
        content_type="application/json",
        **_headers(phase4c_context, "manager"),
    )
    assert missing_reason.status_code == 400
    rejected = client.post(
        reject_path,
        {"reason": "Pricing evidence incomplete", "notes": "Rework requested"},
        content_type="application/json",
        **_headers(phase4c_context, "manager"),
    )
    assert rejected.status_code == 200, rejected.json()
    quotation.refresh_from_db()
    assert quotation.workflow_status == "REJECTED"

    revision = client.post(
        f"/api/v1/canonical/quotations/{quotation.pk}/commands/create-revision/",
        _quotation_payload(phase4c_context, unit_price="11.00", terms="Revision 1"),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="phase4c-revision-1",
        **_headers(phase4c_context, "sales"),
    )
    assert revision.status_code == 201, revision.json()
    quotation.refresh_from_db()
    replacement = SalesQuotation.objects.get(pk=revision.json()["data"]["id"])
    assert quotation.workflow_status == "SUPERSEDED"
    assert replacement.revision == 1
    assert replacement.rfq_id == quotation.rfq_id
    assert replacement.quotation_number.endswith("-R1")
    assert SalesQuotation.objects.filter(rfq=quotation.rfq).count() == 2
    actions = set(AuditEvent.objects.values_list("action", flat=True))
    assert {"quotation.rejected", "quotation.superseded", "quotation.revision_created"} <= actions


@pytest.mark.django_db
def test_approval_success_and_invalid_transition(client, phase4c_context):
    quotation = _submit(
        client, phase4c_context, _create_quotation(client, phase4c_context)
    )
    _approve(client, phase4c_context, quotation)
    assert quotation.workflow_status == "APPROVED"
    assert SalesQuotationApprovalDecision.objects.filter(
        quotation=quotation, decision="APPROVED"
    ).count() == 1
    repeated = client.post(
        f"/api/v1/canonical/quotations/{quotation.pk}/commands/approve/",
        {},
        content_type="application/json",
        **_headers(phase4c_context, "manager"),
    )
    assert repeated.status_code == 409


@pytest.mark.django_db
def test_send_accept_and_convert_exactly_once(client, phase4c_context):
    quotation = _create_quotation(client, phase4c_context)
    _submit(client, phase4c_context, quotation)
    _approve(client, phase4c_context, quotation)
    expected_total = quotation.total
    expected_terms = quotation.terms
    _send(client, phase4c_context, quotation)
    assert quotation.workflow_status == "SENT"
    assert quotation.sent_at is not None
    _accept(client, phase4c_context, quotation)
    assert quotation.workflow_status == "ACCEPTED"
    assert quotation.total == expected_total
    assert quotation.terms == expected_terms
    assert SalesQuotationCustomerDecision.objects.filter(
        quotation=quotation, decision="ACCEPTED"
    ).count() == 1

    path = f"/api/v1/canonical/quotations/{quotation.pk}/commands/convert-to-order/"
    first = client.post(
        path,
        {},
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="phase4c-convert-1",
        **_headers(phase4c_context, "sales"),
    )
    assert first.status_code == 201, first.json()
    replay = client.post(
        path,
        {},
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="phase4c-convert-1",
        **_headers(phase4c_context, "sales"),
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["id"] == first.json()["data"]["id"]
    assert TransactionOrder.objects.filter(source_quotation=quotation).count() == 1
    assert AuditEvent.objects.filter(action="order.converted").count() == 1
    response_text = str(first.json()).casefold()
    for sensitive_name in ("request_hash", "idempotency", "password", "token"):
        assert sensitive_name not in response_text


@pytest.mark.django_db
def test_conversion_requires_accepted_state_key_owner_and_order_view(client, phase4c_context):
    quotation = _create_quotation(client, phase4c_context)
    path = f"/api/v1/canonical/quotations/{quotation.pk}/commands/convert-to-order/"
    missing_key = client.post(
        path, {}, content_type="application/json", **_headers(phase4c_context, "sales")
    )
    assert missing_key.status_code == 400
    wrong_state = client.post(
        path,
        {},
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="wrong-state",
        **_headers(phase4c_context, "sales"),
    )
    assert wrong_state.status_code == 409
    not_owner = client.post(
        path,
        {},
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="not-owner",
        **_headers(phase4c_context, "other_sales"),
    )
    assert not_owner.status_code == 403
    assert TransactionOrder.objects.count() == 0


@pytest.mark.django_db
def test_send_state_and_customer_decline_reason_are_enforced(client, phase4c_context):
    quotation = _create_quotation(client, phase4c_context)
    send_path = f"/api/v1/canonical/quotations/{quotation.pk}/commands/send/"
    wrong_state = client.post(
        send_path,
        {"sent_to": "Buyer", "evidence": "Evidence"},
        content_type="application/json",
        **_headers(phase4c_context, "sales"),
    )
    assert wrong_state.status_code == 409
    _submit(client, phase4c_context, quotation)
    _approve(client, phase4c_context, quotation)
    _send(client, phase4c_context, quotation)
    decline_path = f"/api/v1/canonical/quotations/{quotation.pk}/commands/decline/"
    missing_reason = client.post(
        decline_path,
        {"contact_snapshot": "Buyer", "evidence": "Customer email"},
        content_type="application/json",
        **_headers(phase4c_context, "sales"),
    )
    assert missing_reason.status_code == 400
    declined = client.post(
        decline_path,
        {
            "contact_snapshot": "Buyer",
            "evidence": "Customer email",
            "reason": "Budget withdrawn",
        },
        content_type="application/json",
        **_headers(phase4c_context, "sales"),
    )
    assert declined.status_code == 200, declined.json()
    quotation.refresh_from_db()
    assert quotation.workflow_status == "DECLINED"
    assert SalesQuotationCustomerDecision.objects.get(
        quotation=quotation
    ).reason == "Budget withdrawn"


@pytest.mark.django_db
def test_creation_idempotency_replay_conflict_and_missing_key(client, phase4c_context):
    path = f"/api/v1/canonical/rfqs/{phase4c_context['rfq'].pk}/quotations/commands/create/"
    payload = _quotation_payload(phase4c_context)
    missing = client.post(
        path,
        payload,
        content_type="application/json",
        **_headers(phase4c_context, "sales"),
    )
    assert missing.status_code == 400
    first = client.post(
        path,
        payload,
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="same-create-key",
        **_headers(phase4c_context, "sales"),
    )
    assert first.status_code == 201
    replay = client.post(
        path,
        payload,
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="same-create-key",
        **_headers(phase4c_context, "sales"),
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["id"] == first.json()["data"]["id"]
    changed_payload = _quotation_payload(phase4c_context, terms="Different request")
    conflict = client.post(
        path,
        changed_payload,
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="same-create-key",
        **_headers(phase4c_context, "sales"),
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "idempotency_conflict"
    assert SalesQuotation.objects.count() == 1
    assert AuditEvent.objects.filter(action="quotation.created").count() == 1


@pytest.mark.django_db
def test_audit_failure_rolls_back_business_transition(client, phase4c_context, monkeypatch):
    quotation = _create_quotation(client, phase4c_context)
    original_audit = command_module._audit

    def fail_audit(**_kwargs):
        raise RuntimeError("forced audit rollback")

    monkeypatch.setattr(command_module, "_audit", fail_audit)
    response = client.post(
        f"/api/v1/canonical/quotations/{quotation.pk}/commands/submit/",
        {},
        content_type="application/json",
        **_headers(phase4c_context, "sales"),
    )
    assert response.status_code == 500
    quotation.refresh_from_db()
    assert quotation.workflow_status == "DRAFT"
    assert not AuditEvent.objects.filter(
        action="quotation.submitted", entity_id=str(quotation.pk)
    ).exists()

    monkeypatch.setattr(command_module, "_audit", original_audit)
    retried = client.post(
        f"/api/v1/canonical/quotations/{quotation.pk}/commands/submit/",
        {},
        content_type="application/json",
        **_headers(phase4c_context, "sales"),
    )
    assert retried.status_code == 200
    quotation.refresh_from_db()
    assert quotation.workflow_status == "PENDING_APPROVAL"


@pytest.mark.django_db
def test_create_audit_failure_leaves_no_partial_state(client, phase4c_context, monkeypatch):
    original_audit = command_module._audit

    def fail_audit(**_kwargs):
        raise RuntimeError("forced create rollback")

    monkeypatch.setattr(command_module, "_audit", fail_audit)
    response = client.post(
        f"/api/v1/canonical/rfqs/{phase4c_context['rfq'].pk}/quotations/commands/create/",
        _quotation_payload(phase4c_context),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="rollback-create",
        **_headers(phase4c_context, "sales"),
    )
    assert response.status_code == 500
    phase4c_context["rfq"].refresh_from_db()
    assert phase4c_context["rfq"].quotation_family_number in (None, "")
    assert SalesQuotation.objects.count() == 0
    assert AuditEvent.objects.count() == 0

    monkeypatch.setattr(command_module, "_audit", original_audit)
    retry = client.post(
        f"/api/v1/canonical/rfqs/{phase4c_context['rfq'].pk}/quotations/commands/create/",
        _quotation_payload(phase4c_context),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="rollback-create",
        **_headers(phase4c_context, "sales"),
    )
    assert retry.status_code == 201


@pytest.mark.django_db
def test_vnd_round_half_up_quantum_is_exact(client, phase4c_context):
    payload = _quotation_payload(
        phase4c_context,
        currency="VND",
        unit_price="9.5",
    )
    payload["discount_total"] = "0.5"
    payload["tax_amount"] = "0.5"
    payload["lines"][0]["discount"] = "0.5"
    response = client.post(
        f"/api/v1/canonical/rfqs/{phase4c_context['rfq'].pk}/quotations/commands/create/",
        payload,
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="vnd-rounding",
        **_headers(phase4c_context, "sales"),
    )
    assert response.status_code == 201, response.json()
    quotation = SalesQuotation.objects.get(pk=response.json()["data"]["id"])
    line = quotation.lines.get()
    assert str(line.line_subtotal) == "24.0000"
    assert str(line.discount) == "1.0000"
    assert str(line.line_total) == "23.0000"
    assert str(quotation.total) == "24.0000"


def _service_payload(context, *, terms="Concurrent"):
    today = timezone.localdate()
    return {
        "currency": "USD",
        "valid_from": today,
        "valid_until": today + timedelta(days=14),
        "discount_total": "0",
        "tax_amount": "0",
        "terms": terms,
        "lines": [{
            "source_rfq_line_id": context["line"].pk,
            "unit_price": "10.00",
            "discount": "0",
        }],
    }


@pytest.mark.django_db(transaction=True)
def test_postgresql_concurrent_identical_creation_is_single_effect(phase4c_context):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row-lock evidence")
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            actor = FoundationUser.objects.select_related("role").get(
                pk=phase4c_context["users"]["sales"].pk
            )
            barrier.wait()
            quotation, created = QuotationCommandService.create(
                actor,
                phase4c_context["rfq"].pk,
                _service_payload(phase4c_context),
                "concurrent-identical-create",
            )
            return quotation.pk, created
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _index: worker(), range(2)))
    assert len({item[0] for item in results}) == 1
    assert sorted(item[1] for item in results) == [False, True]
    assert SalesQuotation.objects.count() == 1
    assert AuditEvent.objects.filter(action="quotation.created").count() == 1


@pytest.mark.django_db(transaction=True)
def test_postgresql_concurrent_revision_allocation_has_one_active_revision(
    client, phase4c_context
):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row-lock evidence")
    original = _submit(
        client, phase4c_context, _create_quotation(client, phase4c_context)
    )
    rejected = client.post(
        f"/api/v1/canonical/quotations/{original.pk}/commands/reject/",
        {"reason": "Concurrent rework"},
        content_type="application/json",
        **_headers(phase4c_context, "manager"),
    )
    assert rejected.status_code == 200
    barrier = Barrier(2)

    def worker(index):
        close_old_connections()
        try:
            actor = FoundationUser.objects.select_related("role").get(
                pk=phase4c_context["users"]["sales"].pk
            )
            barrier.wait()
            try:
                quotation, _created = QuotationCommandService.create(
                    actor,
                    phase4c_context["rfq"].pk,
                    _service_payload(phase4c_context, terms=f"Revision contender {index}"),
                    f"revision-contender-{index}",
                    source_quotation_id=original.pk,
                )
                return quotation.pk
            except CanonicalConflict:
                return None
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, range(2)))
    assert sum(item is not None for item in results) == 1
    revisions = list(
        SalesQuotation.objects.filter(rfq=phase4c_context["rfq"])
        .order_by("revision")
        .values_list("revision", "workflow_status")
    )
    assert revisions == [(0, "SUPERSEDED"), (1, "DRAFT")]
    assert AuditEvent.objects.filter(action="quotation.revision_created").count() == 1


@pytest.mark.django_db(transaction=True)
def test_postgresql_concurrent_conversion_creates_one_order(client, phase4c_context):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row-lock evidence")
    quotation = _create_quotation(client, phase4c_context)
    _submit(client, phase4c_context, quotation)
    _approve(client, phase4c_context, quotation)
    _send(client, phase4c_context, quotation)
    _accept(client, phase4c_context, quotation)
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            actor = FoundationUser.objects.select_related("role").get(
                pk=phase4c_context["users"]["sales"].pk
            )
            barrier.wait()
            order, created = QuotationCommandService.convert(
                actor,
                quotation.pk,
                "concurrent-conversion",
            )
            return order.pk, created
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _index: worker(), range(2)))
    assert len({item[0] for item in results}) == 1
    assert sorted(item[1] for item in results) == [False, True]
    assert TransactionOrder.objects.filter(source_quotation=quotation).count() == 1
    assert AuditEvent.objects.filter(action="order.converted").count() == 1
