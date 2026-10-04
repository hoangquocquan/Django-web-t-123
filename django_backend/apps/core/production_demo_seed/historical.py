"""Seed-only historical timestamp backfill.

This module is intentionally internal to the production-demo seed package. It is
not a runtime/admin API and must only touch records owned by
dataset=production_demo_v1.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.business_core.models import (
    BusinessCustomer,
    BusinessMaterial,
    BusinessProduct,
    InventoryTransaction,
)
from apps.crm.models import (
    CrmCustomerProfile,
    CrmInteraction,
    CrmNote,
    CrmTask,
    CrmTimelineEvent,
)
from apps.knowledge.models import (
    DocumentVersion,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeEmbedding,
)
from apps.sales.models import (
    SalesActivity,
    SalesFollowUp,
    SalesLead,
    SalesOpportunity,
    SalesQuotation,
    SalesQuotationApprovalDecision,
    SalesQuotationCustomerDecision,
    SalesRfq,
    SalesRfqDocument,
    SalesTechnicalReview,
)
from apps.transaction_domain.models import (
    AuditEvent,
    OrderProgressEvent,
    TransactionOrder,
)

from .profiles import DATASET_MARKER


@dataclass(frozen=True)
class HistoricalBackfillResult:
    """Summary of timestamp updates."""

    touched: dict[str, int]
    fields: dict[str, tuple[str, ...]]


APPROVED_FIELDS = {
    "BusinessCustomer": ("created_at", "updated_at"),
    "BusinessMaterial": ("created_at", "updated_at"),
    "BusinessProduct": ("created_at", "updated_at"),
    "InventoryTransaction": ("created_at",),
    "CrmCustomerProfile": ("created_at", "updated_at"),
    "CrmInteraction": ("created_at",),
    "CrmNote": ("created_at",),
    "CrmTask": ("created_at",),
    "CrmTimelineEvent": ("created_at",),
    "SalesLead": ("created_at", "updated_at"),
    "SalesOpportunity": ("created_at", "updated_at"),
    "SalesFollowUp": ("created_at",),
    "SalesActivity": ("created_at",),
    "SalesRfq": ("created_at", "updated_at"),
    "SalesRfqDocument": ("uploaded_at",),
    "SalesTechnicalReview": ("created_at",),
    "SalesQuotation": ("created_at", "updated_at", "sent_at"),
    "SalesQuotationApprovalDecision": ("decided_at",),
    "SalesQuotationCustomerDecision": ("decided_at",),
    "TransactionOrder": ("created_at", "updated_at", "ordered_at", "source_quotation_sent_at", "completed_at_v1"),
    "OrderProgressEvent": ("created_at",),
    "AuditEvent": ("created_at",),
    "KnowledgeDocument": ("created_at", "updated_at"),
    "DocumentVersion": ("created_at",),
    "KnowledgeChunk": ("created_at",),
    "KnowledgeEmbedding": ("created_at", "indexed_at"),
}


class HistoricalTimestampBackfiller:
    """Backfill only seed-owned timestamps and validate chronological order."""

    def __init__(self, *, months: int = 24):
        self.months = max(1, int(months or 1))
        self.now = timezone.now()
        self.touched: dict[str, int] = {}

    def apply(self) -> HistoricalBackfillResult:
        with transaction.atomic():
            self._backfill_master_and_crm()
            self._backfill_business_chains()
            self._backfill_knowledge()
            self._validate_chronology()
        return HistoricalBackfillResult(self.touched, APPROVED_FIELDS)

    def _point(self, index: int, step: int = 0):
        days = min(self.months * 30 - 1, (index * 7) % max(30, self.months * 30))
        return self.now - timedelta(days=days + 3) + timedelta(hours=step)

    def _update(self, model, queryset, **fields) -> None:
        safe = set(APPROVED_FIELDS[model.__name__])
        if set(fields) - safe:
            raise AssertionError(f"Unapproved timestamp field for {model.__name__}: {set(fields) - safe}")
        pks = list(queryset.values_list("pk", flat=True))
        if not pks:
            return
        count = model._base_manager.filter(pk__in=pks).update(**fields)
        self.touched[model.__name__] = self.touched.get(model.__name__, 0) + count

    def _backfill_master_and_crm(self):
        for index, customer in enumerate(BusinessCustomer.objects.filter(notes__contains=DATASET_MARKER).order_by("id"), start=1):
            base = self._point(index)
            self._update(BusinessCustomer, BusinessCustomer.objects.filter(pk=customer.pk, notes__contains=DATASET_MARKER), created_at=base, updated_at=base + timedelta(hours=1))
            self._update(CrmCustomerProfile, CrmCustomerProfile.objects.filter(customer=customer), created_at=base + timedelta(hours=1), updated_at=base + timedelta(hours=2))
            self._update(CrmInteraction, CrmInteraction.objects.filter(customer=customer), created_at=base + timedelta(hours=2))
            self._update(CrmNote, CrmNote.objects.filter(customer=customer), created_at=base + timedelta(hours=3))
            self._update(CrmTask, CrmTask.objects.filter(customer=customer), created_at=base + timedelta(hours=4))
            self._update(CrmTimelineEvent, CrmTimelineEvent.objects.filter(customer=customer), created_at=base + timedelta(hours=5))

        for index, material in enumerate(BusinessMaterial.objects.filter(description__contains=DATASET_MARKER).order_by("id"), start=1):
            base = self._point(index)
            self._update(BusinessMaterial, BusinessMaterial.objects.filter(pk=material.pk, description__contains=DATASET_MARKER), created_at=base, updated_at=base + timedelta(hours=1))
        for index, part in enumerate(BusinessProduct.objects.filter(technical_requirements__contains=DATASET_MARKER).order_by("id"), start=1):
            base = self._point(index)
            self._update(BusinessProduct, BusinessProduct.objects.filter(pk=part.pk, technical_requirements__contains=DATASET_MARKER), created_at=base, updated_at=base + timedelta(hours=1))
            self._update(InventoryTransaction, InventoryTransaction.objects.filter(item__product=part), created_at=base + timedelta(hours=2))

        for index, lead in enumerate(SalesLead.objects.filter(notes__contains=DATASET_MARKER).order_by("id"), start=1):
            base = self._point(index)
            self._update(SalesLead, SalesLead.objects.filter(pk=lead.pk, notes__contains=DATASET_MARKER), created_at=base, updated_at=base + timedelta(hours=1))
            self._update(SalesActivity, SalesActivity.objects.filter(lead=lead), created_at=base + timedelta(hours=2))
            self._update(SalesFollowUp, SalesFollowUp.objects.filter(lead=lead), created_at=base + timedelta(hours=3))
        for index, opp in enumerate(SalesOpportunity.objects.filter(notes__contains=DATASET_MARKER).order_by("id"), start=1):
            base = self._point(index)
            self._update(SalesOpportunity, SalesOpportunity.objects.filter(pk=opp.pk, notes__contains=DATASET_MARKER), created_at=base, updated_at=base + timedelta(hours=1))
            self._update(SalesActivity, SalesActivity.objects.filter(opportunity=opp), created_at=base + timedelta(hours=2))
            self._update(SalesFollowUp, SalesFollowUp.objects.filter(opportunity=opp), created_at=base + timedelta(hours=3))

    def _backfill_business_chains(self):
        for index, rfq in enumerate(SalesRfq.objects.filter(notes__contains=DATASET_MARKER).order_by("id"), start=1):
            base = self._point(index)
            self._update(SalesRfq, SalesRfq.objects.filter(pk=rfq.pk, notes__contains=DATASET_MARKER), created_at=base, updated_at=base + timedelta(hours=10))
            self._update(SalesRfqDocument, SalesRfqDocument.objects.filter(rfq=rfq), uploaded_at=base + timedelta(hours=1))
            for review_index, review in enumerate(rfq.technical_reviews.order_by("created_at", "id"), start=1):
                self._update(SalesTechnicalReview, SalesTechnicalReview.objects.filter(pk=review.pk, rfq__notes__contains=DATASET_MARKER), created_at=base + timedelta(hours=2 + review_index))
            for quote_index, quotation in enumerate(SalesQuotation.objects.filter(rfq=rfq).order_by("revision", "id"), start=1):
                quote_time = base + timedelta(hours=6 + quote_index * 3)
                values = {"created_at": quote_time, "updated_at": quote_time + timedelta(hours=1)}
                if quotation.sent_at:
                    values["sent_at"] = quote_time + timedelta(hours=3)
                self._update(SalesQuotation, SalesQuotation.objects.filter(pk=quotation.pk, idempotency_key__startswith="pdv1-"), **values)
                self._update(SalesQuotationApprovalDecision, SalesQuotationApprovalDecision.objects.filter(quotation=quotation), decided_at=quote_time + timedelta(hours=2))
                self._update(SalesQuotationCustomerDecision, SalesQuotationCustomerDecision.objects.filter(quotation=quotation), decided_at=quote_time + timedelta(hours=4))
                order = TransactionOrder.objects.filter(source_quotation=quotation, idempotency_key__startswith="pdv1-order").first()
                if order:
                    order_time = quote_time + timedelta(hours=5)
                    order_values = {
                        "created_at": order_time,
                        "updated_at": order_time + timedelta(hours=1),
                        "ordered_at": order_time,
                    }
                    if quotation.sent_at:
                        order_values["source_quotation_sent_at"] = quote_time + timedelta(hours=3)
                    if order.workflow_status == "COMPLETED":
                        order_values["completed_at_v1"] = order_time + timedelta(hours=8)
                    self._update(TransactionOrder, TransactionOrder.objects.filter(pk=order.pk, idempotency_key__startswith="pdv1-order"), **order_values)
                    for event_index, event in enumerate(order.progress_events.order_by("id"), start=1):
                        self._update(OrderProgressEvent, OrderProgressEvent.objects.filter(pk=event.pk, order__idempotency_key__startswith="pdv1-order"), created_at=order_time + timedelta(hours=event_index))
            self._update(AuditEvent, AuditEvent.objects.filter(entity_type="rfq", entity_id=str(rfq.pk)), created_at=base + timedelta(hours=1))
        for index, order in enumerate(TransactionOrder.objects.filter(idempotency_key__startswith="pdv1-order").order_by("id"), start=1):
            base = order.ordered_at or self._point(index)
            self._update(AuditEvent, AuditEvent.objects.filter(entity_type="order", entity_id=str(order.pk)), created_at=base + timedelta(minutes=30))
            if order.source_quotation_id:
                self._update(AuditEvent, AuditEvent.objects.filter(entity_type="quotation", entity_id=str(order.source_quotation_id)), created_at=base - timedelta(hours=1))

    def _backfill_knowledge(self):
        for index, document in enumerate(KnowledgeDocument.objects.filter(metadata__dataset=DATASET_MARKER).order_by("id"), start=1):
            base = self._point(index)
            self._update(KnowledgeDocument, KnowledgeDocument.objects.filter(pk=document.pk, metadata__dataset=DATASET_MARKER), created_at=base, updated_at=base + timedelta(hours=1))
            self._update(DocumentVersion, DocumentVersion.objects.filter(document=document), created_at=base + timedelta(minutes=10))
            self._update(KnowledgeChunk, KnowledgeChunk.objects.filter(document=document), created_at=base + timedelta(minutes=20))
            self._update(KnowledgeEmbedding, KnowledgeEmbedding.objects.filter(chunk__document=document), created_at=base + timedelta(minutes=30), indexed_at=base + timedelta(minutes=30))

    def _validate_chronology(self):
        if SalesRfq.objects.filter(notes__contains=DATASET_MARKER, created_at__gt=self.now).exists():
            raise AssertionError("Seed-owned RFQ has a future timestamp.")
        if SalesQuotation.objects.filter(idempotency_key__startswith="pdv1-", created_at__gt=self.now).exists():
            raise AssertionError("Seed-owned quotation has a future timestamp.")
        for order in TransactionOrder.objects.filter(idempotency_key__startswith="pdv1-order").select_related("source_quotation__rfq"):
            quotation = order.source_quotation
            rfq = quotation.rfq
            if not (rfq.created_at <= quotation.created_at <= order.ordered_at <= self.now):
                raise AssertionError("Seed-owned RFQ/quotation/order chronology is invalid.")
            progress_times = list(order.progress_events.order_by("created_at", "id").values_list("created_at", flat=True))
            if progress_times and progress_times != sorted(progress_times):
                raise AssertionError("Seed-owned order progress chronology is invalid.")
            if order.workflow_status == "COMPLETED" and order.progress_percent != 100:
                raise AssertionError("Completed seed-owned order must have progress 100.")
