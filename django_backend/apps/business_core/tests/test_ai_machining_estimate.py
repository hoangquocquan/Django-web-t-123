from decimal import Decimal

import pytest

from apps.business_core.models import AIMachiningEstimate


@pytest.mark.django_db
def test_ai_machining_estimate_persists_defaults_and_optional_fields():
    estimate = AIMachiningEstimate.objects.create(
        part_name="Synthetic bracket",
        material="Aluminium 6061",
        machining_type="3-axis CNC",
        customer_email="",
    )

    stored = AIMachiningEstimate.objects.get(pk=estimate.pk)

    assert stored.quantity == 1
    assert stored.tolerance == "±0.01mm"
    assert stored.surface_treatment == "None"
    assert stored.estimated_unit_price == Decimal(0)
    assert stored.estimated_total_price == Decimal(0)
    assert stored.estimated_lead_time_days == 3
    assert stored.dfm_score == 85
    assert stored.matched_products == []
    assert stored.customer_name == ""
    assert stored.dimensions == ""
    assert str(stored) == "Synthetic bracket (Aluminium 6061) - Qty: 1"
