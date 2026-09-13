"""Focused Phase 3D order conversion, progress, audit, RBAC, and race tests."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.utils import timezone

from apps.business_core.models import (
    BusinessCustomer,
    BusinessMaterial,
    BusinessNumberSequence,
    BusinessProduct,
    InventoryTransaction,
)
from apps.foundation.models import FoundationPermission, FoundationRole, FoundationUser
from apps.sales.models import SalesQuotation, SalesRfq, SalesRfqLine
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
from apps.transaction_domain.order_domain import convert_accepted_quotation, transition_order


@pytest.fixture
def phase3d_factory(db):
    sales_role, _ = FoundationRole.objects.get_or_create(name="Sales")
    manager_role, _ = FoundationRole.objects.get_or_create(name="Manager")
    required = {
        "Sales": {"quotation:convert"},
        "Manager": {
            "order:progress", "order:hold", "order:resume",
            "order:complete", "order:cancel",
        },
    }
    for role, codes in ((sales_role, required["Sales"]), (manager_role, required["Manager"])):
        for code in codes:
            module, action = code.split(":", 1)
            permission, _ = FoundationPermission.objects.get_or_create(
                code=code,
                defaults={"module": module, "action": action},
            )
            role.permissions.add(permission)
    sales = FoundationUser.objects.create(
        email="phase3d-sales@example.com",
        full_name="Phase 3D Sales",
        password_hash="unused",
        role=sales_role,
    )
    manager = FoundationUser.objects.create(
        email="phase3d-manager@example.com",
        full_name="Phase 3D Manager",
        password_hash="unused",
        role=manager_role,
    )

    def build(index=1, *, valid_from=None, valid_until=None):
        today = timezone.localdate()
        valid_from_value = valid_from or today
        valid_until_value = valid_until or today + timedelta(days=30)
        code = 9400 + index
        customer = BusinessCustomer.objects.create(
            data_contract="MVP_V1",
            customer_code=f"CUS-{code}",
            company_name=f"Phase 3D Buyer {index}",
            email=f"buyer-{index}@example.com",
            status="ACTIVE",
            created_by=sales,
        )
        material = BusinessMaterial.objects.create(
            material_code=f"MAT-{code}",
            name=f"Material {index}",
            created_by=sales,
        )
        part = BusinessProduct.objects.create(
            data_contract="MVP_V1",
            part_code=f"PART-{code}",
            revision="A",
            unit="PCS",
            default_material=material,
            name=f"Precision part {index}",
            slug=f"phase3d-part-{index}",
            created_by=sales,
        )
        rfq = SalesRfq.objects.create(
            data_contract="MVP_V1",
            rfq_number=f"RFQ-2094-{index:04d}",
            customer=customer,
            status="READY_TO_QUOTE",
            project_name=f"Project {index}",
            quote_due_at=today + timedelta(days=5),
            required_delivery_date=today + timedelta(days=45),
            created_by=sales,
        )
        rfq_line = SalesRfqLine.objects.create(
            rfq=rfq,
            line_number=1,
            part=part,
            material=material,
            description=f"Machine precision part {index}",
            quantity=Decimal("2.3456"),
            unit="PCS",
            required_delivery_date=rfq.required_delivery_date,
        )
        quotation = create_quotation_revision(
            rfq_id=rfq.pk,
            created_by_id=sales.pk,
            currency="USD",
            valid_from=valid_from_value,
            valid_until=valid_until_value,
            pricing_lines=[{
                "source_rfq_line_id": rfq_line.pk,
                "unit_price": "10.0050",
                "discount": "0.4700",
            }],
            discount_total="1.0050",
            tax_amount="2.3450",
            terms="Net 30",
            idempotency_key=f"phase3d-quote-{index}",
            request_hash=f"{index:064x}",
        )
        submit_quotation(quotation.pk, sales.pk)
        record_quotation_approval(
            quotation_id=quotation.pk,
            reviewer_id=manager.pk,
            decision="APPROVED",
        )
        mark_quotation_sent(
            quotation_id=quotation.pk,
            actor_id=sales.pk,
            sent_to=f"buyer-{index}@example.com",
            evidence=f"mail-evidence-{index}",
        )
        record_customer_decision(
            quotation_id=quotation.pk,
            recorded_by_id=sales.pk,
            decision="ACCEPTED",
            contact_snapshot=f"buyer-{index}@example.com",
            evidence=f"signed-acceptance-{index}",
        )
        quotation.refresh_from_db()
        return {
            "sales": sales,
            "manager": manager,
            "customer": customer,
            "material": material,
            "part": part,
            "rfq": rfq,
            "rfq_line": rfq_line,
            "quotation": quotation,
        }

    return build


def convert(context, *, key=None, digest=None):
    index = context["rfq"].pk
    return convert_accepted_quotation(
        quotation_id=context["quotation"].pk,
        actor_id=context["sales"].pk,
        idempotency_key=key or f"phase3d-order-{index}",
        request_hash=digest or ("b" * 64),
    )


@pytest.mark.django_db
def test_conversion_copies_exact_snapshots_totals_and_creates_no_inventory_reservation(phase3d_factory):
    context = phase3d_factory(1)
    inventory_before = InventoryTransaction.objects.count()
    order = convert(context)
    line = order.items.get()

    assert order.order_number.startswith("SO-")
    assert order.data_contract == "MVP_V1"
    assert order.source_quotation_id == context["quotation"].pk
    assert order.source_rfq_id == context["rfq"].pk
    assert order.workflow_status == "CONFIRMED"
    assert order.customer_snapshot == context["quotation"].customer_snapshot
    assert order.currency == context["quotation"].currency
    assert order.subtotal == context["quotation"].subtotal
    assert order.discount_total == context["quotation"].discount_total
    assert order.tax_amount == context["quotation"].tax_amount
    assert order.total_amount == context["quotation"].total
    assert line.description_snapshot == context["quotation"].lines.get().description
    assert line.part_code_snapshot == context["quotation"].lines.get().part_code_snapshot
    assert line.material_snapshot == context["quotation"].lines.get().material_snapshot
    assert line.quantity == context["quotation"].lines.get().quantity
    assert line.unit_price == context["quotation"].lines.get().unit_price
    assert line.line_total == context["quotation"].lines.get().line_total
    assert line.inventory_item_id is None
    assert InventoryTransaction.objects.count() == inventory_before
    assert list(order.progress_events.values_list("from_status", "to_status", "progress_percent")) == [
        ("", "CONFIRMED", 0)
    ]
    assert list(AuditEvent.objects.filter(entity_id=str(order.pk)).values_list("action", flat=True)) == [
        "order.converted"
    ]
    context["rfq"].refresh_from_db()
    assert context["rfq"].status == "CLOSED"


@pytest.mark.django_db
def test_same_idempotency_request_returns_same_order_and_different_hash_conflicts(phase3d_factory):
    context = phase3d_factory(2)
    first = convert(context, key="same-order-key", digest="c" * 64)
    replay = convert(context, key="same-order-key", digest="c" * 64)
    assert replay.pk == first.pk
    assert TransactionOrder.objects.filter(source_quotation=context["quotation"]).count() == 1

    with pytest.raises(ValidationError, match="already used"):
        convert(context, key="same-order-key", digest="d" * 64)
    assert TransactionOrder.objects.filter(source_quotation=context["quotation"]).count() == 1


@pytest.mark.django_db
def test_second_order_for_one_quotation_is_rejected_by_service_and_database(phase3d_factory):
    context = phase3d_factory(3)
    first = convert(context, key="order-source-unique-1")
    with pytest.raises(ValidationError, match="already has"):
        convert(context, key="order-source-unique-2")

    duplicate = TransactionOrder(
        data_contract="MVP_V1",
        source_quotation=first.source_quotation,
        source_rfq=first.source_rfq,
        order_number="SO-2094-9999",
        customer=first.customer,
        workflow_status="CONFIRMED",
        currency=first.currency,
        subtotal=first.subtotal,
        discount_total=first.discount_total,
        tax_amount=first.tax_amount,
        total_amount=first.total_amount,
        customer_snapshot=first.customer_snapshot,
        quotation_snapshot=first.quotation_snapshot,
        ordered_at=first.ordered_at,
        expected_delivery_date=first.expected_delivery_date,
        source_quotation_sent_at=first.source_quotation_sent_at,
        idempotency_key="duplicate-source-order",
        request_hash="e" * 64,
        created_by=first.created_by,
    )
    duplicate._phase3d_conversion_authorized = True
    with pytest.raises(IntegrityError), transaction.atomic():
        duplicate.save(force_insert=True)


@pytest.mark.django_db
def test_direct_mvp_order_and_line_creation_are_rejected(phase3d_factory):
    context = phase3d_factory(4)
    with pytest.raises(RuntimeError, match="conversion"):
        TransactionOrder.objects.create(
            data_contract="MVP_V1",
            order_number="SO-DIRECT-BLOCKED",
            customer=context["customer"],
        )
    with pytest.raises(RuntimeError, match="conversion"):
        TransactionOrder.objects.bulk_create([
            TransactionOrder(
                data_contract="MVP_V1",
                order_number="SO-DIRECT-BULK-BLOCKED",
                customer=context["customer"],
            )
        ])
    order = convert(context)
    with pytest.raises(RuntimeError, match="conversion"):
        TransactionOrderItem.objects.create(
            data_contract="MVP_V1",
            order=order,
            source_quotation_line=context["quotation"].lines.get(),
            line_number=2,
        )
    with pytest.raises(RuntimeError, match="conversion"):
        TransactionOrderItem.objects.bulk_create([
            TransactionOrderItem(
                data_contract="MVP_V1",
                order=order,
                source_quotation_line=context["quotation"].lines.get(),
                line_number=2,
            )
        ])


@pytest.mark.django_db
def test_invalid_progress_transition_percentage_and_reasons_are_atomic(phase3d_factory):
    order = convert(phase3d_factory(5))
    manager = FoundationUser.objects.get(email="phase3d-manager@example.com")
    baseline = (order.workflow_status, order.progress_percent, order.progress_events.count(), AuditEvent.objects.count())

    failures = [
        {"target_status": "COMPLETED", "progress_percent": 100, "reason": ""},
        {"target_status": "IN_PROGRESS", "progress_percent": 101, "reason": ""},
        {"target_status": "IN_PROGRESS", "progress_percent": "1.5", "reason": ""},
        {"target_status": "ON_HOLD", "progress_percent": 0, "reason": ""},
        {"target_status": "CANCELLED", "progress_percent": 0, "reason": ""},
    ]
    for payload in failures:
        with pytest.raises(ValidationError):
            transition_order(order_id=order.pk, actor_id=manager.pk, **payload)
        order.refresh_from_db()
        assert (order.workflow_status, order.progress_percent, order.progress_events.count(), AuditEvent.objects.count()) == baseline


@pytest.mark.django_db
def test_all_approved_state_machine_edges_and_terminal_states(phase3d_factory):
    manager = FoundationUser.objects.get(email="phase3d-manager@example.com")

    completed = convert(phase3d_factory(6))
    transition_order(order_id=completed.pk, actor_id=manager.pk, target_status="IN_PROGRESS", progress_percent=40)
    transition_order(order_id=completed.pk, actor_id=manager.pk, target_status="COMPLETED", progress_percent=100)
    completed.refresh_from_db()
    assert completed.completed_at_v1 is not None
    with pytest.raises(ValidationError):
        transition_order(order_id=completed.pk, actor_id=manager.pk, target_status="CANCELLED", progress_percent=100, reason="late")

    resumed = convert(phase3d_factory(7))
    transition_order(order_id=resumed.pk, actor_id=manager.pk, target_status="ON_HOLD", progress_percent=10, reason="Material wait")
    transition_order(order_id=resumed.pk, actor_id=manager.pk, target_status="IN_PROGRESS", progress_percent=20, reason="Material arrived")
    transition_order(order_id=resumed.pk, actor_id=manager.pk, target_status="CANCELLED", progress_percent=20, reason="Customer cancelled")
    assert resumed.progress_events.filter(to_status="ON_HOLD", reason="Material wait").exists()

    cancelled = convert(phase3d_factory(8))
    transition_order(order_id=cancelled.pk, actor_id=manager.pk, target_status="CANCELLED", progress_percent=0, reason="Cancelled before start")
    with pytest.raises(ValidationError):
        transition_order(order_id=cancelled.pk, actor_id=manager.pk, target_status="IN_PROGRESS", progress_percent=1)

    held = convert(phase3d_factory(9))
    transition_order(order_id=held.pk, actor_id=manager.pk, target_status="IN_PROGRESS", progress_percent=30)
    transition_order(order_id=held.pk, actor_id=manager.pk, target_status="ON_HOLD", progress_percent=30, reason="Tooling issue")
    transition_order(order_id=held.pk, actor_id=manager.pk, target_status="CANCELLED", progress_percent=30, reason="Unable to recover")


@pytest.mark.django_db
def test_rbac_legacy_unassigned_and_sales_progress_fail_closed(phase3d_factory):
    context = phase3d_factory(10)
    order = convert(context)
    legacy_role = FoundationRole.objects.create(name="editor-phase3d")
    wildcard = FoundationPermission.objects.get(module="*", action="*")
    legacy_role.permissions.add(wildcard)
    legacy_user = FoundationUser.objects.create(
        email="legacy-phase3d@example.com", full_name="Legacy", password_hash="unused", role=legacy_role
    )

    with pytest.raises(PermissionDenied):
        transition_order(order_id=order.pk, actor_id=legacy_user.pk, target_status="IN_PROGRESS", progress_percent=1)
    with pytest.raises(PermissionDenied):
        transition_order(order_id=order.pk, actor_id=context["sales"].pk, target_status="IN_PROGRESS", progress_percent=1)

    legacy_order = TransactionOrder.objects.create(
        order_number="ORD-LEGACY-PHASE3D", customer=context["customer"]
    )
    with pytest.raises(PermissionDenied):
        transition_order(order_id=legacy_order.pk, actor_id=context["manager"].pk, target_status="IN_PROGRESS", progress_percent=1)


@pytest.mark.django_db
def test_audit_and_progress_are_append_only_and_unsafe_metadata_is_rejected(phase3d_factory):
    order = convert(phase3d_factory(11))
    audit = AuditEvent.objects.get(action="order.converted", entity_id=str(order.pk))
    progress = order.progress_events.get()

    audit.reason = "mutation"
    with pytest.raises(RuntimeError, match="append-only"):
        audit.save()
    with pytest.raises(RuntimeError, match="append-only"):
        AuditEvent.objects.filter(pk=audit.pk).update(reason="mutation")
    with pytest.raises(RuntimeError, match="append-only"):
        AuditEvent.objects.filter(pk=audit.pk).delete()
    with pytest.raises(RuntimeError, match="append-only"):
        audit.delete()
    with pytest.raises(RuntimeError, match="append-only"):
        progress.delete()

    with pytest.raises(ValidationError, match="Unsafe"):
        AuditEvent.objects.create(
            actor_ref="system",
            actor_display="System",
            action="order.progress_changed",
            entity_type="order",
            entity_id=str(order.pk),
            metadata={"access_token": "must-not-be-stored"},
        )
    system_event = AuditEvent.objects.create(
        actor_ref="system",
        actor_display="System",
        action="order.progress_changed",
        entity_type="order",
        entity_id=str(order.pk),
        metadata={"job_ref": "safe-job-1"},
    )
    assert system_event.actor_user_id is None


@pytest.mark.django_db
def test_failure_after_header_rolls_back_header_number_and_rfq(phase3d_factory, monkeypatch):
    context = phase3d_factory(12)

    def fail(_order):
        raise RuntimeError("forced failure after header")

    monkeypatch.setattr("apps.transaction_domain.order_domain._after_order_header_created", fail)
    with pytest.raises(RuntimeError, match="after header"):
        convert(context)
    assert TransactionOrder.objects.count() == 0
    assert TransactionOrderItem.objects.count() == 0
    assert OrderProgressEvent.objects.count() == 0
    assert AuditEvent.objects.count() == 0
    assert BusinessNumberSequence.objects.filter(namespace="SO").count() == 0
    context["rfq"].refresh_from_db()
    assert context["rfq"].status == "READY_TO_QUOTE"


@pytest.mark.django_db
def test_failure_after_lines_and_events_rolls_back_everything(phase3d_factory, monkeypatch):
    context = phase3d_factory(13)

    def fail(_order):
        assert TransactionOrderItem.objects.count() == 1
        assert OrderProgressEvent.objects.count() == 1
        assert AuditEvent.objects.count() == 1
        raise RuntimeError("forced failure after evidence")

    monkeypatch.setattr("apps.transaction_domain.order_domain._after_order_evidence_created", fail)
    with pytest.raises(RuntimeError, match="after evidence"):
        convert(context)
    assert TransactionOrder.objects.count() == 0
    assert TransactionOrderItem.objects.count() == 0
    assert OrderProgressEvent.objects.count() == 0
    assert AuditEvent.objects.count() == 0
    assert BusinessNumberSequence.objects.filter(namespace="SO").count() == 0


@pytest.mark.django_db
def test_expired_accepted_quotation_is_not_convertible(phase3d_factory, monkeypatch):
    today = timezone.localdate()
    context = phase3d_factory(14, valid_from=today - timedelta(days=2), valid_until=today)
    original_localdate = timezone.localdate

    def shifted_localdate(value=None, timezone=None):
        if value is not None:
            return original_localdate(value, timezone)
        return today + timedelta(days=1)

    monkeypatch.setattr("apps.transaction_domain.order_domain.timezone.localdate", shifted_localdate)
    with pytest.raises(ValidationError, match="Expired"):
        convert(context)
    assert TransactionOrder.objects.count() == 0


@pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="Authoritative conversion concurrency requires PostgreSQL",
)
@pytest.mark.django_db(transaction=True)
def test_postgresql_twenty_concurrent_idempotent_conversions_create_one_order(phase3d_factory):
    context = phase3d_factory(15)
    quotation_id = context["quotation"].pk
    actor_id = context["sales"].pk
    barrier = Barrier(20)

    def run(_index):
        close_old_connections()
        barrier.wait()
        try:
            order = convert_accepted_quotation(
                quotation_id=quotation_id,
                actor_id=actor_id,
                idempotency_key="phase3d-race-key",
                request_hash="f" * 64,
            )
            return order.pk
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=20) as pool:
        order_ids = list(pool.map(run, range(20)))

    assert len(set(order_ids)) == 1
    assert TransactionOrder.objects.filter(source_quotation_id=quotation_id).count() == 1
    order = TransactionOrder.objects.get(pk=order_ids[0])
    assert order.items.count() == 1
    assert order.progress_events.count() == 1
    assert AuditEvent.objects.filter(entity_id=str(order.pk), action="order.converted").count() == 1
