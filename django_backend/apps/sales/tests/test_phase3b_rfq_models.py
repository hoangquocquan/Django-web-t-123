"""Phase 3B RFQ aggregate, document, and review contract tests."""

from datetime import date
from decimal import Decimal
import uuid

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.business_core.models import BusinessCustomer
from apps.foundation.models import FoundationRole, FoundationUser
from apps.sales.models import (
    SalesRfq,
    SalesRfqDocument,
    SalesRfqLine,
    SalesTechnicalReview,
)


@pytest.fixture
def rfq_actor(db):
    role = FoundationRole.objects.create(name="rfq-test-role")
    return FoundationUser.objects.create(
        email="rfq-actor@example.com",
        full_name="RFQ Actor",
        password_hash="unused",
        role=role,
    )


@pytest.fixture
def rfq_customer(db):
    return BusinessCustomer.objects.create(contact_name="Historic customer")


def create_rfq(actor, customer, number="RFQ-2030-0001", **overrides):
    values = {
        "rfq_number": number,
        "customer": customer,
        "quote_due_at": date(2030, 1, 10),
        "required_delivery_date": date(2030, 2, 10),
        "created_by": actor,
    }
    values.update(overrides)
    return SalesRfq.objects.create(**values)


@pytest.mark.django_db
def test_rfq_accepts_both_idempotency_fields_null(rfq_actor, rfq_customer):
    rfq = create_rfq(rfq_actor, rfq_customer)
    assert rfq.idempotency_key is None
    assert rfq.request_hash is None


@pytest.mark.django_db
def test_rfq_accepts_both_idempotency_fields_present(rfq_actor, rfq_customer):
    rfq = create_rfq(
        rfq_actor,
        rfq_customer,
        idempotency_key="rfq-command-1",
        request_hash="a" * 64,
    )
    assert rfq.idempotency_key == "rfq-command-1"


@pytest.mark.django_db
def test_rfq_rejects_partial_idempotency_pair(rfq_actor, rfq_customer):
    with pytest.raises(IntegrityError), transaction.atomic():
        create_rfq(rfq_actor, rfq_customer, idempotency_key="orphan-key")


@pytest.mark.django_db
def test_rfq_idempotency_key_is_unique_when_nonnull(rfq_actor, rfq_customer):
    create_rfq(
        rfq_actor,
        rfq_customer,
        idempotency_key="same-key",
        request_hash="b" * 64,
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        create_rfq(
            rfq_actor,
            rfq_customer,
            number="RFQ-2030-0002",
            idempotency_key="same-key",
            request_hash="c" * 64,
        )


@pytest.mark.django_db
def test_rfq_due_date_and_closed_reason_constraints(rfq_actor, rfq_customer):
    with pytest.raises(IntegrityError), transaction.atomic():
        create_rfq(
            rfq_actor,
            rfq_customer,
            quote_due_at=date(2030, 3, 1),
            required_delivery_date=date(2030, 2, 1),
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        create_rfq(rfq_actor, rfq_customer, status="CLOSED")


@pytest.mark.django_db
def test_rfq_lines_require_positive_unique_number_and_quantity(rfq_actor, rfq_customer):
    rfq = create_rfq(rfq_actor, rfq_customer)
    SalesRfqLine.objects.create(
        rfq=rfq,
        line_number=1,
        description="Machine one shaft",
        quantity=Decimal("2.5000"),
        required_delivery_date=date(2030, 2, 1),
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        SalesRfqLine.objects.create(
            rfq=rfq,
            line_number=1,
            description="Duplicate line",
            quantity=Decimal("1.0000"),
            required_delivery_date=date(2030, 2, 1),
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        SalesRfqLine.objects.create(
            rfq=rfq,
            line_number=2,
            description="Invalid quantity",
            quantity=Decimal("0"),
            required_delivery_date=date(2030, 2, 1),
        )


@pytest.mark.django_db
def test_document_rejects_cross_rfq_line(rfq_actor, rfq_customer):
    first = create_rfq(rfq_actor, rfq_customer)
    second = create_rfq(rfq_actor, rfq_customer, number="RFQ-2030-0002")
    second_line = SalesRfqLine.objects.create(
        rfq=second,
        line_number=1,
        description="Second RFQ line",
        quantity=Decimal("1"),
        required_delivery_date=date(2030, 2, 1),
    )
    document = SalesRfqDocument(
        rfq=first,
        rfq_line=second_line,
        original_filename="drawing.pdf",
        storage_key="rfq/first/drawing.pdf",
        mime_type="application/pdf",
        size_bytes=100,
        checksum_sha256="d" * 64,
        uploaded_by=rfq_actor,
    )

    with pytest.raises(ValidationError, match="same RFQ"):
        document.full_clean()


@pytest.mark.django_db
def test_document_version_and_storage_constraints(rfq_actor, rfq_customer):
    rfq = create_rfq(rfq_actor, rfq_customer)
    group_id = uuid.uuid4()
    SalesRfqDocument.objects.create(
        rfq=rfq,
        document_group_id=group_id,
        version=1,
        original_filename="drawing.pdf",
        storage_key="rfq/drawing-v1.pdf",
        mime_type="application/pdf",
        size_bytes=100,
        checksum_sha256="e" * 64,
        uploaded_by=rfq_actor,
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        SalesRfqDocument.objects.create(
            rfq=rfq,
            document_group_id=group_id,
            version=1,
            original_filename="drawing-copy.pdf",
            storage_key="rfq/drawing-copy.pdf",
            mime_type="application/pdf",
            size_bytes=100,
            checksum_sha256="f" * 64,
            uploaded_by=rfq_actor,
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("field_overrides"),
    [
        {"size_bytes": 0},
        {"mime_type": "application/x-executable"},
        {"checksum_sha256": "not-a-sha256"},
    ],
)
def test_document_metadata_constraints(field_overrides, rfq_actor, rfq_customer):
    rfq = create_rfq(rfq_actor, rfq_customer)
    values = {
        "rfq": rfq,
        "original_filename": "drawing.pdf",
        "storage_key": f"rfq/{uuid.uuid4()}/drawing.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 100,
        "checksum_sha256": "a" * 64,
        "uploaded_by": rfq_actor,
    }
    values.update(field_overrides)

    with pytest.raises(IntegrityError), transaction.atomic():
        SalesRfqDocument.objects.create(**values)


@pytest.mark.django_db
def test_technical_review_is_append_only_and_reasoned(rfq_actor, rfq_customer):
    rfq = create_rfq(rfq_actor, rfq_customer)
    with pytest.raises(IntegrityError), transaction.atomic():
        SalesTechnicalReview.objects.create(
            rfq=rfq,
            reviewer=rfq_actor,
            decision="NEEDS_INFORMATION",
        )

    review = SalesTechnicalReview.objects.create(
        rfq=rfq,
        reviewer=rfq_actor,
        decision="STARTED",
    )
    review.notes = "Mutation is forbidden"
    with pytest.raises(RuntimeError, match="append-only"):
        review.save()
    with pytest.raises(RuntimeError, match="append-only"):
        SalesTechnicalReview.objects.filter(pk=review.pk).update(notes="forbidden")
    with pytest.raises(RuntimeError, match="append-only"):
        review.delete()


@pytest.mark.django_db
def test_technical_review_decision_is_controlled(rfq_actor, rfq_customer):
    rfq = create_rfq(rfq_actor, rfq_customer)
    with pytest.raises(IntegrityError), transaction.atomic():
        SalesTechnicalReview.objects.create(
            rfq=rfq,
            reviewer=rfq_actor,
            decision="APPROVED",
        )
