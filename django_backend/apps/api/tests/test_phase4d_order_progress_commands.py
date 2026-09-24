"""Focused Phase 4D canonical order progress command tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier

import pytest
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection
from django.utils import timezone

from apps.api.services.canonical_command_service import OrderProgressCommandService
from apps.business_core.models import (
    BusinessCustomer,
    BusinessMaterial,
    BusinessProduct,
    InventoryTransaction,
)
from apps.foundation.models import (
    FoundationAuthToken,
    FoundationPermission,
    FoundationRole,
    FoundationUser,
)
from apps.foundation.services import FoundationAuthService
from apps.sales.models import SalesRfq, SalesRfqLine
from apps.sales.quotation_domain import (
    create_quotation_revision,
    mark_quotation_sent,
    record_customer_decision,
    record_quotation_approval,
    submit_quotation,
)
from apps.transaction_domain.models import (
    AuditEvent,
    OrderProgressEvent,
    TransactionOrder,
    TransactionOrderItem,
)
from apps.transaction_domain.order_domain import convert_accepted_quotation
from apps.transaction_domain.services import OrderService, WorkflowService


ROLE_PERMISSIONS = {
    "Admin": {
        "order:view", "order:progress", "order:hold", "order:resume",
        "order:complete", "order:cancel", "audit:view",
    },
    "Manager": {
        "order:view", "order:progress", "order:hold", "order:resume",
        "order:complete", "order:cancel", "audit:view",
    },
    "Sales": {"quotation:convert", "order:view"},
}


def _permission(code):
    module, action = code.split(":", 1)
    permission, _created = FoundationPermission.objects.get_or_create(
        code=code,
        defaults={"module": module, "action": action, "description": "Phase 4D test"},
    )
    return permission


def _user(role_name, suffix, permissions=(), *, active=True):
    role, _created = FoundationRole.objects.get_or_create(name=role_name)
    role.is_active = True
    role.save(update_fields=["is_active"])
    for code in permissions:
        role.permissions.add(_permission(code))
    return FoundationUser.objects.create(
        email=f"{suffix}@phase4d.example",
        full_name=f"Phase 4D {suffix}",
        password_hash="test-only-placeholder",
        role=role,
        is_active=active,
    )


def _token(user, suffix):
    raw = f"phase4d-{suffix}-credential"
    FoundationAuthToken.objects.create(
        user=user,
        token_hash=FoundationAuthService.hash_token(raw),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    return raw


def _headers(context, actor):
    return {"HTTP_AUTHORIZATION": f"Bearer {context['tokens'][actor]}"}


def _build_order(users, index):
    today = timezone.localdate()
    customer = BusinessCustomer.objects.create(
        data_contract="MVP_V1",
        customer_code=f"CUS-P4D-{index:03d}",
        company_name=f"Phase 4D Customer {index}",
        email=f"buyer-{index}@example.invalid",
        status="ACTIVE",
        created_by=users["sales"],
        updated_by=users["sales"],
    )
    material = BusinessMaterial.objects.create(
        data_contract="MVP_V1",
        material_code=f"MAT-P4D-{index:03d}",
        name="SUS316",
        created_by=users["admin"],
        updated_by=users["admin"],
    )
    part = BusinessProduct.objects.create(
        data_contract="MVP_V1",
        part_code=f"PART-P4D-{index:03d}",
        name=f"Progress fixture {index}",
        slug=f"phase4d-progress-fixture-{index}",
        revision="A",
        unit="PCS",
        default_material=material,
        tolerance="0.01",
        technical_requirements="Mill and inspect",
        created_by=users["admin"],
        updated_by=users["admin"],
    )
    rfq = SalesRfq.objects.create(
        data_contract="MVP_V1",
        rfq_number=f"RFQ-P4D-{index:03d}",
        customer=customer,
        status="READY_TO_QUOTE",
        project_name="Canonical order progress",
        quote_due_at=today + timedelta(days=3),
        required_delivery_date=today + timedelta(days=45),
        assigned_to=users["sales"],
        created_by=users["sales"],
        updated_by=users["sales"],
    )
    line = SalesRfqLine.objects.create(
        rfq=rfq,
        line_number=1,
        part=part,
        material=material,
        description="Progress fixture body",
        quantity=Decimal("2.0000"),
        unit="PCS",
        required_delivery_date=rfq.required_delivery_date,
        tolerance="0.01",
        technical_notes="Inspect critical faces",
        drawing_required=False,
    )
    quotation = create_quotation_revision(
        rfq_id=rfq.pk,
        created_by_id=users["sales"].pk,
        currency="USD",
        valid_from=today,
        valid_until=today + timedelta(days=14),
        pricing_lines=[{
            "source_rfq_line_id": line.pk,
            "unit_price": "10.0000",
            "discount": "0",
        }],
        discount_total="0",
        tax_amount="0",
        terms="Net 30",
        idempotency_key=f"phase4d-quotation-{index}",
        request_hash=f"{index:064x}",
    )
    submit_quotation(quotation.pk, users["sales"].pk)
    record_quotation_approval(
        quotation_id=quotation.pk,
        reviewer_id=users["manager"].pk,
        decision="APPROVED",
    )
    mark_quotation_sent(
        quotation_id=quotation.pk,
        actor_id=users["sales"].pk,
        sent_to="Buyer",
        evidence=f"CRM send P4D-{index:03d}",
    )
    record_customer_decision(
        quotation_id=quotation.pk,
        recorded_by_id=users["sales"].pk,
        decision="ACCEPTED",
        contact_snapshot="Buyer",
        evidence=f"Signed acceptance P4D-{index:03d}",
    )
    return convert_accepted_quotation(
        quotation_id=quotation.pk,
        actor_id=users["sales"].pk,
        idempotency_key=f"phase4d-order-{index}",
        request_hash=f"{index + 1000:064x}",
    )


@pytest.fixture
def phase4d_context(db):
    users = {
        role.casefold(): _user(role, role.casefold(), permissions)
        for role, permissions in ROLE_PERMISSIONS.items()
    }
    users["inactive"] = _user(
        "Manager", "inactive", ROLE_PERMISSIONS["Manager"], active=False
    )
    users["unassigned"] = _user("Unassigned", "unassigned", {"order:view", "order:progress"})
    users["unrelated"] = _user("Reviewer", "unrelated", {"order:view", "order:progress"})
    users["wildcard"] = _user("Wildcard", "wildcard")
    users["wildcard"].role.permissions.add(_permission("*:*"))
    tokens = {name: _token(user, name) for name, user in users.items()}
    order = _build_order(users, 1)
    return {"users": users, "tokens": tokens, "order": order, "customer": order.customer}


def _post(client, context, order, command, payload=None, actor="manager"):
    return client.post(
        f"/api/v1/canonical/orders/{order.pk}/commands/{command}/",
        payload or {},
        content_type="application/json",
        **_headers(context, actor),
    )


def _successful_command_count(order):
    return OrderProgressEvent.objects.filter(order=order).count() - 1


@pytest.mark.django_db
def test_auth_active_user_active_role_exact_view_and_exact_command_are_required(
    client, phase4d_context
):
    order = phase4d_context["order"]
    path = f"/api/v1/canonical/orders/{order.pk}/commands/progress/"
    payload = {"progress_percent": 25, "milestone_note": "Started machining"}
    assert client.post(path, payload, content_type="application/json").status_code == 401

    assert _post(client, phase4d_context, order, "progress", payload, "inactive").status_code == 401
    role = phase4d_context["users"]["manager"].role
    role.is_active = False
    role.save(update_fields=["is_active"])
    assert _post(client, phase4d_context, order, "progress", payload).status_code == 403
    role.is_active = True
    role.save(update_fields=["is_active"])

    role.permissions.remove(_permission("order:view"))
    assert _post(client, phase4d_context, order, "progress", payload).status_code == 403
    role.permissions.add(_permission("order:view"))

    role.permissions.remove(_permission("order:progress"))
    assert _post(client, phase4d_context, order, "progress", payload).status_code == 403
    role.permissions.add(_permission("order:progress"))


@pytest.mark.django_db
def test_wildcard_unassigned_unrelated_and_sales_roles_are_denied(client, phase4d_context):
    order = phase4d_context["order"]
    payloads = {
        "progress": {"progress_percent": 10},
        "hold": {"progress_percent": 0, "reason": "Blocked"},
        "resume": {"progress_percent": 10},
        "complete": {},
        "cancel": {"progress_percent": 0, "reason": "Cancelled"},
    }
    for actor in ("wildcard", "unassigned", "unrelated"):
        response = _post(client, phase4d_context, order, "progress", payloads["progress"], actor)
        assert response.status_code == 403
    for command, payload in payloads.items():
        response = _post(client, phase4d_context, order, command, payload, "sales")
        assert response.status_code == 403


@pytest.mark.django_db
def test_admin_and_manager_are_allowed_only_with_exact_permission(client, phase4d_context):
    order = phase4d_context["order"]
    admin_role = phase4d_context["users"]["admin"].role
    payload = {"progress_percent": 12, "milestone_note": "Admin start"}
    admin_role.permissions.remove(_permission("order:progress"))
    assert _post(client, phase4d_context, order, "progress", payload, "admin").status_code == 403
    admin_role.permissions.add(_permission("order:progress"))
    response = _post(client, phase4d_context, order, "progress", payload, "admin")
    assert response.status_code == 200, response.json()

    second = _build_order(phase4d_context["users"], 2)
    manager_role = phase4d_context["users"]["manager"].role
    manager_role.permissions.remove(_permission("order:progress"))
    assert _post(client, phase4d_context, second, "progress", {"progress_percent": 9}).status_code == 403
    manager_role.permissions.add(_permission("order:progress"))
    assert _post(client, phase4d_context, second, "progress", {"progress_percent": 9}).status_code == 200


@pytest.mark.django_db
def test_complete_transition_matrix_for_each_allowed_edge(client, phase4d_context):
    users = phase4d_context["users"]
    cases = [
        (2, [("progress", {"progress_percent": 15}, "IN_PROGRESS")]),
        (3, [("hold", {"progress_percent": 0, "reason": "Pre-start hold"}, "ON_HOLD")]),
        (4, [("cancel", {"progress_percent": 0, "reason": "Cancelled before start"}, "CANCELLED")]),
        (5, [("progress", {"progress_percent": 15}, "IN_PROGRESS"), ("progress", {"progress_percent": 45}, "IN_PROGRESS")]),
        (6, [("progress", {"progress_percent": 20}, "IN_PROGRESS"), ("hold", {"progress_percent": 20, "reason": "Tooling wait"}, "ON_HOLD")]),
        (7, [("progress", {"progress_percent": 80}, "IN_PROGRESS"), ("complete", {"progress_percent": 100, "milestone_note": "Done"}, "COMPLETED")]),
        (8, [("progress", {"progress_percent": 55}, "IN_PROGRESS"), ("cancel", {"progress_percent": 55, "reason": "Customer stopped"}, "CANCELLED")]),
        (9, [("hold", {"progress_percent": 5, "reason": "Waiting"}, "ON_HOLD"), ("resume", {"progress_percent": 10}, "IN_PROGRESS")]),
        (10, [("hold", {"progress_percent": 5, "reason": "Waiting"}, "ON_HOLD"), ("cancel", {"progress_percent": 5, "reason": "Cannot recover"}, "CANCELLED")]),
    ]
    for index, commands in cases:
        order = _build_order(users, index)
        before_inventory = InventoryTransaction.objects.count()
        before_success = _successful_command_count(order)
        for command, payload, expected_status in commands:
            before_events = OrderProgressEvent.objects.filter(order=order).count()
            before_audits = AuditEvent.objects.filter(entity_type="order", entity_id=str(order.pk)).count()
            response = _post(client, phase4d_context, order, command, payload)
            assert response.status_code == 200, response.json()
            assert response.json()["data"]["workflow_status"] == expected_status
            assert OrderProgressEvent.objects.filter(order=order).count() == before_events + 1
            assert AuditEvent.objects.filter(entity_type="order", entity_id=str(order.pk)).count() == before_audits + 1
        order.refresh_from_db()
        assert _successful_command_count(order) == before_success + len(commands)
        assert InventoryTransaction.objects.count() == before_inventory


@pytest.mark.django_db
def test_completed_and_cancelled_are_terminal(client, phase4d_context):
    completed = _build_order(phase4d_context["users"], 11)
    assert _post(client, phase4d_context, completed, "progress", {"progress_percent": 50}).status_code == 200
    assert _post(client, phase4d_context, completed, "complete", {}).status_code == 200
    assert _post(client, phase4d_context, completed, "cancel", {"progress_percent": 100, "reason": "Too late"}).status_code == 400

    cancelled = _build_order(phase4d_context["users"], 12)
    assert _post(client, phase4d_context, cancelled, "cancel", {"progress_percent": 0, "reason": "Cancelled"}).status_code == 200
    assert _post(client, phase4d_context, cancelled, "progress", {"progress_percent": 1}).status_code == 400


@pytest.mark.django_db
def test_invalid_payloads_and_failed_commands_leave_no_timeline_evidence(client, phase4d_context):
    order = phase4d_context["order"]
    baseline = (
        order.workflow_status,
        order.progress_percent,
        OrderProgressEvent.objects.filter(order=order).count(),
        AuditEvent.objects.filter(entity_type="order", entity_id=str(order.pk)).count(),
    )
    failures = [
        ("hold", {"progress_percent": 10}),
        ("cancel", {"progress_percent": 10}),
        ("progress", {"progress_percent": -1}),
        ("progress", {"progress_percent": 101}),
        ("progress", {"progress_percent": "1.5"}),
        ("progress", {"progress_percent": 10, "target_status": "CANCELLED"}),
        ("complete", {"progress_percent": 99}),
    ]
    for command, payload in failures:
        assert _post(client, phase4d_context, order, command, payload).status_code == 400
    order.refresh_from_db()
    assert (
        order.workflow_status,
        order.progress_percent,
        OrderProgressEvent.objects.filter(order=order).count(),
        AuditEvent.objects.filter(entity_type="order", entity_id=str(order.pk)).count(),
    ) == baseline
    progress = client.get(f"/api/v1/canonical/orders/{order.pk}/progress/", **_headers(phase4d_context, "manager"))
    audit = client.get(f"/api/v1/canonical/timelines/order/{order.pk}/", **_headers(phase4d_context, "manager"))
    assert progress.json()["data"]["count"] == 1
    assert audit.json()["data"]["count"] == 1


@pytest.mark.django_db
def test_completion_sets_exactly_100_and_completion_timestamp(client, phase4d_context):
    order = phase4d_context["order"]
    assert _post(client, phase4d_context, order, "progress", {"progress_percent": 70}).status_code == 200
    response = _post(client, phase4d_context, order, "complete", {})
    assert response.status_code == 200, response.json()
    order.refresh_from_db()
    assert order.progress_percent == 100
    assert order.completed_at_v1 is not None
    assert response.json()["data"]["progress_percent"] == 100
    assert response.json()["data"]["completed_at"] is not None


@pytest.mark.django_db
def test_legacy_order_alias_and_internal_fields_are_rejected_or_hidden(client, phase4d_context):
    legacy_order = TransactionOrder.objects.create(
        order_number="ORD-P4D-LEGACY",
        customer=phase4d_context["customer"],
    )
    response = _post(client, phase4d_context, legacy_order, "progress", {"progress_percent": 1})
    assert response.status_code == 403
    alias = client.post(
        f"/api/v1/canonical/orders/{phase4d_context['order'].pk}/commands/start-progress/",
        {"progress_percent": 1},
        content_type="application/json",
        **_headers(phase4d_context, "manager"),
    )
    assert alias.status_code == 404
    ok = _post(
        client,
        phase4d_context,
        phase4d_context["order"],
        "progress",
        {"progress_percent": 22, "milestone_note": "Public response"},
    )
    serialized = str(ok.json()).casefold()
    for forbidden in ("idempotency", "request_hash", "password", "token", "secret"):
        assert forbidden not in serialized


@pytest.mark.django_db
def test_progress_read_entity_timeline_and_global_audit_permissions(client, phase4d_context):
    order = phase4d_context["order"]
    response = _post(
        client,
        phase4d_context,
        order,
        "progress",
        {"progress_percent": 35, "milestone_note": "Committed milestone"},
    )
    assert response.status_code == 200
    progress = client.get(f"/api/v1/canonical/orders/{order.pk}/progress/", **_headers(phase4d_context, "manager"))
    assert progress.status_code == 200
    assert [item["to_status"] for item in progress.json()["data"]["results"]] == ["CONFIRMED", "IN_PROGRESS"]
    timeline = client.get(f"/api/v1/canonical/timelines/order/{order.pk}/", **_headers(phase4d_context, "manager"))
    assert timeline.status_code == 200
    assert [item["action"] for item in timeline.json()["data"]["results"]] == ["order.converted", "order.progress_changed"]
    for actor in ("admin", "manager"):
        audit = client.get("/api/v1/canonical/audit-events/", **_headers(phase4d_context, actor))
        assert audit.status_code == 200
    assert client.get("/api/v1/canonical/audit-events/", **_headers(phase4d_context, "sales")).status_code == 403


@pytest.mark.django_db
def test_forced_audit_and_post_update_failures_roll_back_state_and_evidence(client, phase4d_context, monkeypatch):
    order = phase4d_context["order"]

    def fail_audit(**_kwargs):
        raise RuntimeError("forced progress audit rollback")

    monkeypatch.setattr("apps.transaction_domain.order_domain._create_audit_event", fail_audit)
    response = _post(client, phase4d_context, order, "progress", {"progress_percent": 30, "milestone_note": "Should roll back"})
    assert response.status_code == 500
    order.refresh_from_db()
    assert order.workflow_status == "CONFIRMED"
    assert order.progress_percent == 0
    assert list(order.progress_events.values_list("to_status", flat=True)) == ["CONFIRMED"]
    assert list(AuditEvent.objects.values_list("action", flat=True)) == ["order.converted"]

    monkeypatch.undo()

    def fail_after_save(_order):
        assert TransactionOrder.objects.get(pk=order.pk).workflow_status == "IN_PROGRESS"
        raise RuntimeError("forced transition rollback")

    monkeypatch.setattr("apps.transaction_domain.order_domain._after_order_transition_saved", fail_after_save)
    response = _post(client, phase4d_context, order, "progress", {"progress_percent": 40})
    assert response.status_code == 500
    order.refresh_from_db()
    assert order.workflow_status == "CONFIRMED"
    assert order.progress_percent == 0
    assert OrderProgressEvent.objects.filter(order=order).count() == 1
    assert AuditEvent.objects.filter(entity_type="order", entity_id=str(order.pk)).count() == 1


@pytest.mark.django_db
def test_canonical_write_boundaries_block_direct_and_legacy_mutation(phase4d_context):
    order = phase4d_context["order"]
    item = order.items.get()
    progress = order.progress_events.get()
    audit = AuditEvent.objects.get(entity_type="order", entity_id=str(order.pk))

    order.workflow_status = "IN_PROGRESS"
    with pytest.raises(RuntimeError, match="Phase 3D commands"):
        order.save()
    with pytest.raises(RuntimeError, match="Phase 3D commands"):
        TransactionOrder.objects.filter(pk=order.pk).update(workflow_status="IN_PROGRESS")
    with pytest.raises(RuntimeError, match="cannot be deleted"):
        order.delete()

    item.note = "mutation"
    with pytest.raises(RuntimeError, match="immutable"):
        item.save()
    with pytest.raises(RuntimeError, match="immutable"):
        TransactionOrderItem.objects.filter(pk=item.pk).delete()

    progress.reason = "mutation"
    with pytest.raises(RuntimeError, match="append-only"):
        progress.save()
    with pytest.raises(RuntimeError, match="append-only"):
        OrderProgressEvent.objects.filter(pk=progress.pk).update(reason="mutation")

    audit.reason = "mutation"
    with pytest.raises(RuntimeError, match="append-only"):
        audit.save()
    with pytest.raises(RuntimeError, match="append-only"):
        AuditEvent.objects.filter(pk=audit.pk).delete()

    with pytest.raises(ValidationError, match="Canonical MVP_V1"):
        OrderService().update_order(order, project_name="legacy overwrite")
    with pytest.raises(ValidationError, match="Canonical MVP_V1"):
        WorkflowService().transition_order(order, "approved")


def _pg_transition(actor_id, order_id, command, payload):
    close_old_connections()
    try:
        actor = FoundationUser.objects.select_related("role").get(pk=actor_id)
        method = getattr(OrderProgressCommandService, command)
        try:
            order = method(actor, order_id, payload)
            return ("ok", order.workflow_status, order.progress_percent)
        except Exception as exc:  # noqa: BLE001 - race tests inspect expected losers.
            return (exc.__class__.__name__, str(exc), None)
    finally:
        close_old_connections()


def _run_two(callables):
    barrier = Barrier(2)

    def worker(fn):
        barrier.wait()
        return fn()

    with ThreadPoolExecutor(max_workers=2) as pool:
        return list(pool.map(worker, callables))


pytestmark_pg = pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="PostgreSQL row-lock evidence",
)


@pytestmark_pg
@pytest.mark.django_db(transaction=True)
def test_postgresql_two_simultaneous_progress_attempts_have_one_authority(phase4d_context):
    order = phase4d_context["order"]
    actor_id = phase4d_context["users"]["manager"].pk
    results = _run_two([
        lambda: _pg_transition(actor_id, order.pk, "progress", {"progress_percent": 10}),
        lambda: _pg_transition(actor_id, order.pk, "progress", {"progress_percent": 10}),
    ])
    assert sum(item[0] == "ok" for item in results) == 1
    order.refresh_from_db()
    assert order.workflow_status == "IN_PROGRESS"
    assert OrderProgressEvent.objects.filter(order=order, to_status="IN_PROGRESS").count() == 1
    assert AuditEvent.objects.filter(entity_id=str(order.pk), action="order.progress_changed").count() == 1


@pytestmark_pg
@pytest.mark.django_db(transaction=True)
def test_postgresql_hold_versus_complete_has_one_authoritative_result(phase4d_context):
    order = phase4d_context["order"]
    actor = phase4d_context["users"]["manager"]
    OrderProgressCommandService.progress(actor, order.pk, {"progress_percent": 50})
    results = _run_two([
        lambda: _pg_transition(actor.pk, order.pk, "hold", {"progress_percent": 50, "reason": "Hold"}),
        lambda: _pg_transition(actor.pk, order.pk, "complete", {"progress_percent": 100}),
    ])
    assert sum(item[0] == "ok" for item in results) == 1
    order.refresh_from_db()
    assert order.workflow_status in {"ON_HOLD", "COMPLETED"}
    assert OrderProgressEvent.objects.filter(order=order).count() == 3
    assert AuditEvent.objects.filter(entity_id=str(order.pk)).count() == 3


@pytestmark_pg
@pytest.mark.django_db(transaction=True)
def test_postgresql_cancel_versus_complete_has_one_terminal_result(phase4d_context):
    order = phase4d_context["order"]
    actor = phase4d_context["users"]["manager"]
    OrderProgressCommandService.progress(actor, order.pk, {"progress_percent": 75})
    results = _run_two([
        lambda: _pg_transition(actor.pk, order.pk, "cancel", {"progress_percent": 75, "reason": "Cancel"}),
        lambda: _pg_transition(actor.pk, order.pk, "complete", {"progress_percent": 100}),
    ])
    assert sum(item[0] == "ok" for item in results) == 1
    order.refresh_from_db()
    assert order.workflow_status in {"CANCELLED", "COMPLETED"}
    assert OrderProgressEvent.objects.filter(order=order).count() == 3
    assert AuditEvent.objects.filter(entity_id=str(order.pk)).count() == 3


@pytestmark_pg
@pytest.mark.django_db(transaction=True)
def test_postgresql_two_simultaneous_completion_attempts_create_one_completion(phase4d_context):
    order = phase4d_context["order"]
    actor = phase4d_context["users"]["manager"]
    OrderProgressCommandService.progress(actor, order.pk, {"progress_percent": 90})
    results = _run_two([
        lambda: _pg_transition(actor.pk, order.pk, "complete", {"progress_percent": 100}),
        lambda: _pg_transition(actor.pk, order.pk, "complete", {"progress_percent": 100}),
    ])
    assert sum(item[0] == "ok" for item in results) == 1
    order.refresh_from_db()
    assert order.workflow_status == "COMPLETED"
    assert OrderProgressEvent.objects.filter(order=order, to_status="COMPLETED").count() == 1
    assert AuditEvent.objects.filter(entity_id=str(order.pk), action="order.completed").count() == 1
