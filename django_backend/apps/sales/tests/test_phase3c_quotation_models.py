"""Phase 3C quotation model, money, workflow, and concurrency tests."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.utils import timezone

from apps.business_core.models import (
    BusinessCustomer,
    BusinessMaterial,
    BusinessNumberSequence,
    BusinessProduct,
)
from apps.foundation.models import FoundationRole, FoundationUser
from apps.sales.models import (
    SalesQuotation,
    SalesQuotationApprovalDecision,
    SalesQuotationCustomerDecision,
    SalesQuotationLine,
    SalesRfq,
    SalesRfqLine,
)
from apps.sales.quotation_domain import (
    calculate_line_amounts,
    create_quotation_revision,
    mark_quotation_sent,
    record_customer_decision,
    record_quotation_approval,
    submit_quotation,
)


@pytest.fixture
def quotation_context(db):
    role = FoundationRole.objects.create(name="phase3c-role")
    creator = FoundationUser.objects.create(
        email="phase3c-creator@example.com",
        full_name="Phase 3C Creator",
        password_hash="unused",
        role=role,
    )
    reviewer = FoundationUser.objects.create(
        email="phase3c-reviewer@example.com",
        full_name="Phase 3C Reviewer",
        password_hash="unused",
        role=role,
    )
    customer = BusinessCustomer.objects.create(
        data_contract="MVP_V1",
        customer_code="CUS-9301",
        company_name="Phase 3C Buyer",
        contact_name="Buyer",
        email="buyer-phase3c@example.com",
        status="ACTIVE",
        created_by=creator,
    )
    material = BusinessMaterial.objects.create(
        material_code="MAT-9301",
        name="SUS304",
        created_by=creator,
    )
    part = BusinessProduct.objects.create(
        data_contract="MVP_V1",
        part_code="PART-9301",
        revision="A",
        unit="PCS",
        default_material=material,
        name="Phase 3C shaft",
        slug="phase3c-shaft",
        created_by=creator,
    )
    today = timezone.localdate()
    rfq = SalesRfq.objects.create(
        data_contract="MVP_V1",
        rfq_number="RFQ-2093-0001",
        customer=customer,
        status="READY_TO_QUOTE",
        quote_due_at=today + timedelta(days=10),
        required_delivery_date=today + timedelta(days=40),
        created_by=creator,
    )
    rfq_line = SalesRfqLine.objects.create(
        rfq=rfq,
        line_number=1,
        part=part,
        material=material,
        description="Machine precision shaft",
        quantity=Decimal("2.3456"),
        unit="PCS",
        required_delivery_date=today + timedelta(days=40),
    )
    return {
        "creator": creator,
        "reviewer": reviewer,
        "customer": customer,
        "material": material,
        "part": part,
        "rfq": rfq,
        "rfq_line": rfq_line,
        "today": today,
    }


def create_revision(context, *, key="phase3c-key-1", request_hash=None, **overrides):
    values = {
        "rfq_id": context["rfq"].pk,
        "created_by_id": context["creator"].pk,
        "currency": "USD",
        "valid_from": context["today"],
        "valid_until": context["today"] + timedelta(days=30),
        "pricing_lines": [
            {
                "source_rfq_line_id": context["rfq_line"].pk,
                "unit_price": "10.0050",
                "discount": "0.4700",
            }
        ],
        "discount_total": "1.0050",
        "tax_amount": "2.3450",
        "terms": "Net 30",
        "idempotency_key": key,
        "request_hash": request_hash or ("a" * 64),
    }
    values.update(overrides)
    return create_quotation_revision(**values)


@pytest.mark.django_db
def test_legacy_quotation_defaults_preserve_compatibility_fields():
    quotation = SalesQuotation.objects.create(
        quotation_number="SQ-LEGACY-PHASE3C",
        version=7,
        status="accepted",
        approval_status="approved",
        subtotal=Decimal("12.34"),
        discount_total=Decimal("1.00"),
        total=Decimal("11.34"),
    )
    line = SalesQuotationLine.objects.create(
        quotation=quotation,
        description="Historic line",
        quantity=Decimal("2"),
        unit_price=Decimal("5"),
        line_total=Decimal("10"),
    )

    assert quotation.data_contract == "LEGACY"
    assert quotation.rfq_id is None
    assert quotation.revision is None
    assert quotation.workflow_status is None
    assert quotation.version == 7
    assert quotation.status == "accepted"
    assert quotation.approval_status == "approved"
    assert line.data_contract == "LEGACY"
    assert line.source_rfq_line_id is None
    assert line.line_number is None


def test_currency_round_half_up_and_float_rejection():
    usd = calculate_line_amounts(
        quantity="2.3456", unit_price="10.0050", discount="0.47", currency="USD"
    )
    vnd = calculate_line_amounts(
        quantity="1", unit_price="100.5", discount="0", currency="VND"
    )

    assert usd["line_subtotal"] == Decimal("23.4700")
    assert usd["line_total"] == Decimal("23.0000")
    assert vnd["line_subtotal"] == Decimal("101.0000")
    with pytest.raises(ValidationError, match="Float"):
        calculate_line_amounts(quantity=1.0, unit_price="10", discount="0", currency="USD")


@pytest.mark.django_db
def test_create_revision_allocates_family_revision_snapshots_and_backend_totals(quotation_context):
    quotation = create_revision(quotation_context)
    line = quotation.lines.get()
    quotation_context["rfq"].refresh_from_db()

    assert quotation.revision == 0
    assert quotation.quotation_number == f"{quotation_context['rfq'].quotation_family_number}-R0"
    assert quotation.quotation_number.startswith("QT-")
    assert quotation.customer_id == quotation_context["customer"].pk
    assert quotation.customer_snapshot["customer_code"] == "CUS-9301"
    assert quotation.rfq_snapshot["rfq_number"] == "RFQ-2093-0001"
    assert quotation.subtotal == Decimal("23.4700")
    assert quotation.discount_total == Decimal("1.0100")
    assert quotation.tax_amount == Decimal("2.3500")
    assert quotation.total == Decimal("24.8100")
    assert line.part_code_snapshot == "PART-9301"
    assert line.material_snapshot == "MAT-9301 - SUS304"
    assert line.line_subtotal == Decimal("23.4700")
    assert line.line_total == Decimal("23.0000")


@pytest.mark.django_db
def test_revision_create_is_idempotent_and_conflicting_hash_is_atomic(quotation_context):
    first = create_revision(quotation_context)
    replay = create_revision(quotation_context)
    assert replay.pk == first.pk

    before = SalesQuotation.objects.count()
    with pytest.raises(ValidationError, match="already used"):
        create_revision(quotation_context, request_hash="b" * 64)
    assert SalesQuotation.objects.count() == before


@pytest.mark.django_db
def test_submit_locks_header_and_line_snapshots(quotation_context):
    quotation = create_revision(quotation_context)
    line = quotation.lines.get()
    submit_quotation(quotation.pk, quotation_context["creator"].pk)
    quotation.refresh_from_db()
    assert quotation.workflow_status == "PENDING_APPROVAL"

    quotation.terms = "Mutated terms"
    with pytest.raises(RuntimeError, match="immutable"):
        quotation.save()
    line.description = "Mutated line"
    with pytest.raises(RuntimeError, match="immutable"):
        line.save()
    with pytest.raises(RuntimeError, match="immutable"):
        SalesQuotationLine.objects.filter(pk=line.pk).update(description="bulk mutation")


@pytest.mark.django_db
def test_invalid_workflow_jump_is_rejected(quotation_context):
    quotation = create_revision(quotation_context)
    quotation.workflow_status = "ACCEPTED"
    with pytest.raises(RuntimeError, match="Invalid"):
        quotation.save(update_fields=["workflow_status", "updated_at"])


@pytest.mark.django_db
def test_maker_checker_failure_creates_no_decision_or_status_change(quotation_context):
    quotation = create_revision(quotation_context)
    submit_quotation(quotation.pk, quotation_context["creator"].pk)

    with pytest.raises(ValidationError, match="creator"):
        record_quotation_approval(
            quotation_id=quotation.pk,
            reviewer_id=quotation_context["creator"].pk,
            decision="APPROVED",
        )
    quotation.refresh_from_db()
    assert quotation.workflow_status == "PENDING_APPROVAL"
    assert SalesQuotationApprovalDecision.objects.count() == 0


@pytest.mark.django_db
def test_rejection_reason_and_decision_append_only(quotation_context):
    quotation = create_revision(quotation_context)
    submit_quotation(quotation.pk, quotation_context["creator"].pk)

    with pytest.raises(ValidationError, match="reason"):
        record_quotation_approval(
            quotation_id=quotation.pk,
            reviewer_id=quotation_context["reviewer"].pk,
            decision="REJECTED",
        )
    decision = record_quotation_approval(
        quotation_id=quotation.pk,
        reviewer_id=quotation_context["reviewer"].pk,
        decision="REJECTED",
        reason="Commercial revision required",
    )
    decision.reason = "Mutation"
    with pytest.raises(RuntimeError, match="append-only"):
        decision.save()
    with pytest.raises(RuntimeError, match="append-only"):
        SalesQuotationApprovalDecision.objects.filter(pk=decision.pk).delete()


@pytest.mark.django_db
def test_rework_allocates_next_revision_and_supersedes_rejected(quotation_context):
    first = create_revision(quotation_context)
    family = first.quotation_number.rsplit("-R", 1)[0]
    submit_quotation(first.pk, quotation_context["creator"].pk)
    record_quotation_approval(
        quotation_id=first.pk,
        reviewer_id=quotation_context["reviewer"].pk,
        decision="REJECTED",
        reason="Revise price",
    )

    second = create_revision(
        quotation_context,
        key="phase3c-key-2",
        request_hash="b" * 64,
    )
    first.refresh_from_db()
    assert first.workflow_status == "SUPERSEDED"
    assert second.revision == 1
    assert second.quotation_number == f"{family}-R1"


@pytest.mark.django_db
def test_approval_send_and_customer_acceptance(quotation_context):
    quotation = create_revision(quotation_context)
    submit_quotation(quotation.pk, quotation_context["creator"].pk)
    record_quotation_approval(
        quotation_id=quotation.pk,
        reviewer_id=quotation_context["reviewer"].pk,
        decision="APPROVED",
    )
    mark_quotation_sent(
        quotation_id=quotation.pk,
        actor_id=quotation_context["creator"].pk,
        sent_to="buyer-phase3c@example.com",
        evidence="mail-message-id:phase3c",
    )
    decision = record_customer_decision(
        quotation_id=quotation.pk,
        recorded_by_id=quotation_context["creator"].pk,
        decision="ACCEPTED",
        contact_snapshot="buyer-phase3c@example.com",
        evidence="signed acceptance phase3c",
    )
    quotation.refresh_from_db()
    assert decision.decision == "ACCEPTED"
    assert quotation.workflow_status == "ACCEPTED"


@pytest.mark.django_db
def test_expired_quotation_cannot_be_accepted(quotation_context):
    past = quotation_context["today"] - timedelta(days=10)
    quotation = create_revision(
        quotation_context,
        valid_from=past,
        valid_until=quotation_context["today"] - timedelta(days=1),
    )
    submit_quotation(quotation.pk, quotation_context["creator"].pk)
    record_quotation_approval(
        quotation_id=quotation.pk,
        reviewer_id=quotation_context["reviewer"].pk,
        decision="APPROVED",
    )
    mark_quotation_sent(
        quotation_id=quotation.pk,
        actor_id=quotation_context["creator"].pk,
        sent_to="buyer-phase3c@example.com",
        evidence="historic-send",
        sent_at=timezone.now() - timedelta(days=2),
    )
    with pytest.raises(ValidationError, match="expired"):
        record_customer_decision(
            quotation_id=quotation.pk,
            recorded_by_id=quotation_context["creator"].pk,
            decision="ACCEPTED",
            contact_snapshot="buyer-phase3c@example.com",
            evidence="late acceptance",
        )
    quotation.refresh_from_db()
    assert quotation.workflow_status == "SENT"
    assert SalesQuotationCustomerDecision.objects.count() == 0


@pytest.mark.django_db
def test_database_constraints_reject_effective_duplicate_and_missing_reasons(quotation_context):
    quotation = create_revision(quotation_context)
    submit_quotation(quotation.pk, quotation_context["creator"].pk)
    record_quotation_approval(
        quotation_id=quotation.pk,
        reviewer_id=quotation_context["reviewer"].pk,
        decision="APPROVED",
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        SalesQuotation.objects.create(
            data_contract="MVP_V1",
            rfq=quotation_context["rfq"],
            customer=quotation_context["customer"],
            quotation_number="QT-2093-9999-R1",
            revision=1,
            workflow_status="APPROVED",
            currency="USD",
            valid_from=quotation_context["today"],
            valid_until=quotation_context["today"] + timedelta(days=1),
            subtotal=Decimal("1"),
            total=Decimal("1"),
            customer_snapshot={"customer_code": "CUS-9301"},
            rfq_snapshot={"rfq_number": "RFQ-2093-0001"},
            idempotency_key="effective-duplicate",
            request_hash="d" * 64,
            created_by=quotation_context["creator"],
        )

    pending = SalesQuotation.objects.create(
        data_contract="MVP_V1",
        rfq=quotation_context["rfq"],
        customer=quotation_context["customer"],
        quotation_number="QT-2093-9998-R2",
        revision=2,
        workflow_status="PENDING_APPROVAL",
        currency="USD",
        valid_from=quotation_context["today"],
        valid_until=quotation_context["today"] + timedelta(days=1),
        subtotal=Decimal("1"),
        total=Decimal("1"),
        customer_snapshot={"customer_code": "CUS-9301"},
        rfq_snapshot={"rfq_number": "RFQ-2093-0001"},
        idempotency_key="reason-probe",
        request_hash="e" * 64,
        created_by=quotation_context["creator"],
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        SalesQuotationApprovalDecision.objects.create(
            quotation=pending,
            reviewer=quotation_context["reviewer"],
            decision="REJECTED",
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        SalesQuotationCustomerDecision.objects.create(
            quotation=pending,
            recorded_by=quotation_context["creator"],
            decision="DECLINED",
            contact_snapshot="buyer@example.com",
            evidence="evidence",
        )


@pytest.mark.django_db
def test_create_failure_rolls_back_family_sequence_header_and_lines(quotation_context, monkeypatch):
    def fail_after_family_allocation(*args, **kwargs):
        raise RuntimeError("simulated line persistence failure")

    monkeypatch.setattr("apps.sales.quotation_domain._prepare_line", fail_after_family_allocation)
    with pytest.raises(RuntimeError, match="simulated"):
        create_revision(quotation_context)

    quotation_context["rfq"].refresh_from_db()
    assert quotation_context["rfq"].quotation_family_number is None
    assert SalesQuotation.objects.count() == 0
    assert SalesQuotationLine.objects.count() == 0
    assert BusinessNumberSequence.objects.filter(namespace="QT").count() == 0


@pytest.mark.django_db
def test_cross_rfq_source_line_is_rejected_by_model_validation(quotation_context):
    quotation = create_revision(quotation_context)
    other_rfq = SalesRfq.objects.create(
        data_contract="MVP_V1",
        rfq_number="RFQ-2093-0002",
        customer=quotation_context["customer"],
        status="READY_TO_QUOTE",
        quote_due_at=quotation_context["today"] + timedelta(days=10),
        required_delivery_date=quotation_context["today"] + timedelta(days=40),
        created_by=quotation_context["creator"],
    )
    other_line = SalesRfqLine.objects.create(
        rfq=other_rfq,
        line_number=1,
        part=quotation_context["part"],
        description="Other RFQ line",
        quantity=Decimal("1"),
        unit="PCS",
        required_delivery_date=quotation_context["today"] + timedelta(days=40),
    )
    line = quotation.lines.get()
    line.source_rfq_line = other_line
    with pytest.raises(ValidationError, match="same RFQ"):
        line.full_clean()


@pytest.mark.django_db(transaction=True)
def test_postgresql_simultaneous_next_revision_has_one_winner_no_duplicates(quotation_context):
    if connection.vendor != "postgresql":
        pytest.skip("Authoritative revision concurrency validation requires PostgreSQL")

    first = create_revision(quotation_context)
    submit_quotation(first.pk, quotation_context["creator"].pk)
    record_quotation_approval(
        quotation_id=first.pk,
        reviewer_id=quotation_context["reviewer"].pk,
        decision="REJECTED",
        reason="Concurrency rework probe",
    )
    barrier = Barrier(20)

    def create_after_barrier(index):
        close_old_connections()
        barrier.wait()
        try:
            result = create_revision(
                quotation_context,
                key=f"phase3c-race-{index}",
                request_hash=f"{index:064x}",
            )
            return ("created", result.revision)
        except ValidationError:
            return ("conflict", None)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(create_after_barrier, range(20)))

    created = [revision for status, revision in results if status == "created"]
    assert created == [1]
    assert sum(status == "conflict" for status, _revision in results) == 19
    revisions = list(
        SalesQuotation.objects.filter(rfq=quotation_context["rfq"]).values_list(
            "revision", flat=True
        )
    )
    assert sorted(revisions) == [0, 1]
    assert len(revisions) == len(set(revisions))
