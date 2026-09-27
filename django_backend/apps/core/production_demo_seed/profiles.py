"""Explicit production-demo seed profiles."""

from __future__ import annotations

from dataclasses import dataclass

DATASET_MARKER = "production_demo_v1"
DATASET_PREFIX = "PDV1"
SAFE_EMAIL_DOMAIN = "production-demo.invalid"
FIXED_RANDOM_SEED = 20260918


@dataclass(frozen=True)
class SeedProfile:
    """Small immutable profile definition."""

    name: str
    users: int
    customers: int
    materials: int
    parts: int
    warehouses: int
    rfqs: int
    knowledge_documents: int
    ai_eval_cases: int
    inventory_items: int = 0
    inventory_transactions: int = 0
    leads: int = 0
    opportunities: int = 0
    crm_activities: int = 0
    quotation_revisions: int = 20
    orders: int = 8
    historical_months: int = 0


TEST_PROFILE = SeedProfile(
    name="TEST",
    users=6,
    customers=12,
    materials=12,
    parts=30,
    warehouses=2,
    rfqs=35,
    knowledge_documents=12,
    ai_eval_cases=20,
    inventory_items=30,
    inventory_transactions=30,
    leads=0,
    opportunities=0,
    crm_activities=0,
    quotation_revisions=20,
    orders=8,
    historical_months=0,
)

SMALL_PROFILE = SeedProfile(
    name="SMALL",
    users=12,
    customers=60,
    materials=35,
    parts=150,
    warehouses=3,
    rfqs=300,
    knowledge_documents=60,
    ai_eval_cases=60,
    inventory_items=250,
    inventory_transactions=750,
    leads=180,
    opportunities=100,
    crm_activities=800,
    quotation_revisions=220,
    orders=100,
    historical_months=24,
)

FULL_PROFILE = SeedProfile(
    name="FULL",
    users=30,
    customers=200,
    materials=100,
    parts=600,
    warehouses=4,
    rfqs=1500,
    knowledge_documents=200,
    ai_eval_cases=150,
    inventory_items=900,
    inventory_transactions=3000,
    leads=700,
    opportunities=350,
    crm_activities=4000,
    quotation_revisions=1000,
    orders=500,
    historical_months=24,
)

PROFILES = {
    TEST_PROFILE.name: TEST_PROFILE,
    SMALL_PROFILE.name: SMALL_PROFILE,
}


def get_profile(name: str) -> SeedProfile:
    """Return an implemented profile or raise a clear error."""

    key = str(name or "").strip().upper()
    if key not in PROFILES:
        raise ValueError("Only TEST and SMALL profiles are enabled; FULL is disabled.")
    return PROFILES[key]
