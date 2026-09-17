from __future__ import annotations

from datetime import timedelta
from io import StringIO

import pytest
from apps.api.services.canonical_read_service import CanonicalReadService
from apps.business_core.models import (
    BusinessCustomer,
    BusinessMaterial,
    BusinessProduct,
)
from apps.core.management.commands.phase6b_e2e_fixture import (
    CUSTOMER_CODE,
    FIXTURE_USERS,
    MATERIAL_CODE,
    PART_CODE,
)
from apps.foundation.models import (
    FoundationLoginAttempt,
    FoundationRole,
    FoundationUser,
)
from apps.foundation.security import privacy_hash
from apps.sales.models import SalesRfq
from django.core.management import call_command
from django.utils import timezone


@pytest.mark.django_db
def test_phase6b_fixture_is_fictional_bounded_and_idempotent(monkeypatch):
    for role_name in FIXTURE_USERS:
        FoundationRole.objects.update_or_create(
            name=role_name,
            defaults={"is_active": True},
        )
    sales_hash = privacy_hash(FIXTURE_USERS["Sales"])
    FoundationLoginAttempt.objects.create(
        email_hash=sales_hash,
        remote_addr_hash=privacy_hash("127.0.0.1"),
        success=False,
        reason="invalid_credentials",
    )
    FoundationLoginAttempt.objects.create(
        email_hash=sales_hash,
        remote_addr_hash=privacy_hash("127.0.0.1"),
        success=True,
        reason="authenticated",
    )
    monkeypatch.setattr("sys.stdin", StringIO("Local-Phase6B-Only!42\n" * 2))

    for _iteration in range(2):
        call_command("phase6b_e2e_fixture", password_stdin=True, stdout=StringIO())

    assert FoundationUser.objects.filter(email__in=FIXTURE_USERS.values()).count() == 3
    assert BusinessCustomer.objects.filter(customer_code=CUSTOMER_CODE).count() == 1
    assert BusinessMaterial.objects.filter(material_code=MATERIAL_CODE).count() == 1
    assert BusinessProduct.objects.filter(part_code=PART_CODE).count() == 1
    assert not FoundationUser.objects.filter(email__endswith="@gmail.com").exists()
    assert not FoundationLoginAttempt.objects.filter(
        email_hash=sales_hash,
        success=False,
    ).exists()
    assert (
        FoundationLoginAttempt.objects.filter(
            email_hash=sales_hash,
            success=True,
        ).count()
        == 1
    )


@pytest.mark.django_db
@pytest.mark.parametrize("family_number", [None, ""])
def test_quotation_family_index_excludes_rfqs_without_a_family(family_number):
    role = FoundationRole.objects.get(name="Sales", is_active=True)
    owner = FoundationUser.objects.create(
        email="phase6b.family-owner@example.invalid",
        full_name="Phase 6B Family Owner",
        password_hash="not-a-login-password",
        role=role,
        is_active=True,
    )
    customer = BusinessCustomer.objects.create(
        customer_code=f"CUS-NO-FAMILY-{family_number is None}",
        company_name="Phase 6B No Family Customer",
        status="ACTIVE",
        created_by=owner,
        updated_by=owner,
    )
    today = timezone.localdate()
    rfq = SalesRfq.objects.create(
        data_contract="MVP_V1",
        rfq_number=f"RFQ-NO-FAMILY-{family_number is None}",
        quotation_family_number=family_number,
        customer=customer,
        status="DRAFT",
        quote_due_at=today + timedelta(days=7),
        required_delivery_date=today + timedelta(days=30),
        assigned_to=owner,
        created_by=owner,
        updated_by=owner,
    )

    assert not CanonicalReadService.quotation_families().filter(pk=rfq.pk).exists()
