"""Phase 3B master-data and business-number contract tests."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier

import pytest
from django.db import IntegrityError, close_old_connections, connection, transaction

from apps.business_core.business_numbers import (
    MAX_ALLOCATION_ATTEMPTS,
    allocate_business_number,
    format_business_number,
    period_for_namespace,
)
from apps.business_core.models import (
    BusinessCustomer,
    BusinessMaterial,
    BusinessNumberSequence,
    BusinessProduct,
)
from apps.foundation.models import FoundationRole, FoundationUser


@pytest.fixture
def phase3b_user(db):
    role = FoundationRole.objects.create(name="phase3b-test-role")
    return FoundationUser.objects.create(
        email="phase3b@example.com",
        full_name="Phase 3B Test",
        password_hash="unused",
        role=role,
    )


@pytest.mark.django_db
def test_business_number_formats_and_periods():
    instant = datetime(2031, 6, 1, tzinfo=timezone.utc)

    assert period_for_namespace("cus", instant) == "GLOBAL"
    assert period_for_namespace("RFQ", instant) == "2031"
    assert format_business_number("PART", "GLOBAL", 12) == "PART-0012"
    assert format_business_number("SO", "2031", 12) == "SO-2031-0012"
    with pytest.raises(ValueError):
        period_for_namespace("UNKNOWN", instant)


@pytest.mark.django_db
def test_allocator_increments_each_namespace_period():
    instant = datetime(2032, 1, 2, tzinfo=timezone.utc)

    assert allocate_business_number("CUS", now=instant) == "CUS-0001"
    assert allocate_business_number("CUS", now=instant) == "CUS-0002"
    assert allocate_business_number("RFQ", now=instant) == "RFQ-2032-0001"
    assert BusinessNumberSequence.objects.count() == 2


@pytest.mark.django_db
def test_allocator_has_a_bounded_integrity_retry(monkeypatch):
    attempts = []

    def always_conflict(namespace, period):
        attempts.append((namespace, period))
        raise IntegrityError("simulated allocation race")

    monkeypatch.setattr("apps.business_core.business_numbers._allocate_once", always_conflict)
    with pytest.raises(IntegrityError, match="simulated allocation race"):
        allocate_business_number("MAT")
    assert len(attempts) == MAX_ALLOCATION_ATTEMPTS


@pytest.mark.django_db
def test_sequence_namespace_period_constraint():
    with pytest.raises(IntegrityError), transaction.atomic():
        BusinessNumberSequence.objects.create(namespace="CUS", period="2030")


@pytest.mark.django_db
def test_mvp_master_records_require_canonical_fields(phase3b_user):
    BusinessCustomer.objects.create(
        data_contract="MVP_V1",
        customer_code="CUS-0001",
        company_name="Precision Buyer",
        contact_name="Buyer",
        email="buyer@example.com",
        status="ACTIVE",
        created_by=phase3b_user,
    )
    material = BusinessMaterial.objects.create(
        material_code="MAT-0001",
        name="SUS304",
        created_by=phase3b_user,
    )
    BusinessProduct.objects.create(
        data_contract="MVP_V1",
        part_code="PART-0001",
        revision="A",
        unit="PCS",
        default_material=material,
        name="Turned shaft",
        slug="turned-shaft",
        created_by=phase3b_user,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        BusinessCustomer.objects.create(
            data_contract="MVP_V1",
            customer_code="CUS-0002",
            company_name="No contact",
            contact_name="Nobody",
            status="ACTIVE",
            created_by=phase3b_user,
        )


@pytest.mark.django_db
def test_legacy_master_rows_remain_compatible_without_v1_fields():
    customer = BusinessCustomer.objects.create(contact_name="Historic", status="active")
    product = BusinessProduct.objects.create(name="Historic part", slug="historic-part")

    assert customer.data_contract == "LEGACY"
    assert product.data_contract == "LEGACY"


@pytest.mark.django_db
def test_nullable_business_codes_are_unique_when_issued():
    BusinessCustomer.objects.create(contact_name="One", customer_code=None)
    BusinessCustomer.objects.create(contact_name="Two", customer_code=None)
    BusinessCustomer.objects.create(contact_name="Three", customer_code="CUS-0042")

    with pytest.raises(IntegrityError), transaction.atomic():
        BusinessCustomer.objects.create(contact_name="Four", customer_code="CUS-0042")


@pytest.mark.django_db
def test_part_and_material_codes_are_unique(phase3b_user):
    BusinessProduct.objects.create(
        name="Legacy part one",
        slug="legacy-part-one",
        part_code="PART-0099",
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        BusinessProduct.objects.create(
            name="Legacy part two",
            slug="legacy-part-two",
            part_code="PART-0099",
        )

    BusinessMaterial.objects.create(
        material_code="MAT-0099",
        name="Material one",
        created_by=phase3b_user,
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        BusinessMaterial.objects.create(
            material_code="MAT-0099",
            name="Material two",
            created_by=phase3b_user,
        )


@pytest.mark.django_db
def test_sqlite_fallback_does_not_claim_select_for_update_parity():
    if connection.vendor != "sqlite":
        pytest.skip("SQLite limitation assertion applies only to the fallback backend")
    assert connection.features.has_select_for_update is False


@pytest.mark.django_db(transaction=True)
def test_postgresql_allocator_is_unique_under_concurrency():
    if connection.vendor != "postgresql":
        pytest.skip("Authoritative allocator concurrency validation requires PostgreSQL")

    workers = 12
    barrier = Barrier(workers)

    def allocate_after_barrier(_index):
        close_old_connections()
        barrier.wait()
        value = allocate_business_number("RFQ")
        close_old_connections()
        return value

    with ThreadPoolExecutor(max_workers=workers) as pool:
        values = list(pool.map(allocate_after_barrier, range(workers)))

    assert len(values) == workers
    assert len(set(values)) == workers
