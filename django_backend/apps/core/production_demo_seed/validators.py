"""Validation helpers for production-demo seed."""

from __future__ import annotations

import re

from apps.business_core.models import (
    BusinessCustomer,
    BusinessMaterial,
    BusinessProduct,
)
from apps.knowledge.models import KnowledgeDocument
from apps.sales.models import SalesRfq
from apps.transaction_domain.models import TransactionOrder

from .ai_eval_cases import load_ai_eval_cases
from .ownership import is_owned_email
from .profiles import DATASET_MARKER

DELIVERABLE_EMAIL_RE = re.compile(r"@(gmail|yahoo|outlook|hotmail|company|example)\.", re.IGNORECASE)


def owned_business_counts(profile: str = "TEST") -> dict[str, int]:
    """Return counts of current production-demo-owned records."""

    return {
        "customers": BusinessCustomer.objects.filter(notes__contains=DATASET_MARKER).count(),
        "materials": BusinessMaterial.objects.filter(description__contains=DATASET_MARKER).count(),
        "parts": BusinessProduct.objects.filter(technical_requirements__contains=DATASET_MARKER).count(),
        "rfqs": SalesRfq.objects.filter(notes__contains=DATASET_MARKER).count(),
        "orders": TransactionOrder.objects.filter(idempotency_key__startswith="pdv1-order-").count(),
        "knowledge_documents": KnowledgeDocument.objects.filter(metadata__dataset=DATASET_MARKER).count(),
        "ai_eval_cases": len(load_ai_eval_cases(profile)),
    }


def assert_no_deliverable_seed_pii() -> None:
    """Fail if seed-owned contacts look deliverable or real."""

    bad = []
    for email in BusinessCustomer.objects.filter(notes__contains=DATASET_MARKER).values_list("email", flat=True):
        if email and (DELIVERABLE_EMAIL_RE.search(email) or not is_owned_email(email)):
            bad.append(email)
    if bad:
        raise AssertionError(f"Seed-owned customer email is not safe/non-deliverable: {bad[:3]}")
