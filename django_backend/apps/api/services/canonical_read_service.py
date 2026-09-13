"""Optimized ORM boundary for Phase 4A canonical read APIs."""

from django.db.models import Prefetch

from apps.business_core.models import BusinessCustomer, BusinessMaterial, BusinessProduct
from apps.sales.models import (
    SalesQuotation,
    SalesQuotationApprovalDecision,
    SalesQuotationCustomerDecision,
    SalesQuotationLine,
    SalesRfq,
    SalesRfqDocument,
    SalesRfqLine,
    SalesTechnicalReview,
)
from apps.transaction_domain.models import (
    AuditEvent,
    OrderProgressEvent,
    TransactionOrder,
    TransactionOrderItem,
)


class CanonicalReadService:
    """Return only explicitly shaped, relation-loaded canonical querysets."""

    ENTITY_MODELS = {
        "customer": BusinessCustomer,
        "part": BusinessProduct,
        "material": BusinessMaterial,
        "rfq": SalesRfq,
        "quotation": SalesQuotation,
        "order": TransactionOrder,
    }

    @staticmethod
    def customers():
        return BusinessCustomer.objects.select_related("created_by", "updated_by")

    @classmethod
    def customer(cls, object_id):
        return cls.customers().get(pk=object_id)

    @staticmethod
    def parts():
        return BusinessProduct.objects.select_related(
            "default_material", "created_by", "updated_by"
        )

    @classmethod
    def part(cls, object_id):
        return cls.parts().get(pk=object_id)

    @staticmethod
    def materials():
        return BusinessMaterial.objects.select_related("created_by", "updated_by")

    @classmethod
    def material(cls, object_id):
        return cls.materials().get(pk=object_id)

    @staticmethod
    def rfqs():
        return SalesRfq.objects.select_related(
            "customer", "assigned_to", "created_by", "updated_by"
        )

    @classmethod
    def rfq(cls, object_id):
        return cls.rfqs().get(pk=object_id)

    @classmethod
    def rfq_lines(cls, rfq_id):
        cls.rfq(rfq_id)
        return SalesRfqLine.objects.filter(rfq_id=rfq_id).select_related(
            "part", "material"
        )

    @classmethod
    def rfq_documents(cls, rfq_id):
        cls.rfq(rfq_id)
        return SalesRfqDocument.objects.filter(rfq_id=rfq_id).select_related(
            "rfq_line", "replaces", "uploaded_by"
        )

    @classmethod
    def technical_reviews(cls, rfq_id):
        cls.rfq(rfq_id)
        return SalesTechnicalReview.objects.filter(rfq_id=rfq_id).select_related(
            "reviewer"
        )

    @staticmethod
    def _quotation_queryset():
        return SalesQuotation.objects.select_related(
            "rfq", "customer", "created_by", "updated_by"
        )

    @classmethod
    def quotations(cls):
        return cls._quotation_queryset()

    @classmethod
    def quotation(cls, object_id):
        return cls._quotation_queryset().get(pk=object_id)

    @classmethod
    def quotation_families(cls):
        revisions = cls._quotation_queryset().order_by("revision", "id")
        return SalesRfq.objects.exclude(quotation_family_number="").select_related(
            "customer"
        ).prefetch_related(Prefetch("quotations", queryset=revisions))

    @classmethod
    def quotation_family(cls, family_number):
        return cls.quotation_families().get(quotation_family_number=family_number)

    @classmethod
    def quotation_revisions(cls, family_number):
        family = cls.quotation_family(family_number)
        return cls._quotation_queryset().filter(rfq_id=family.pk)

    @classmethod
    def quotation_lines(cls, quotation_id):
        cls.quotation(quotation_id)
        return SalesQuotationLine.objects.filter(quotation_id=quotation_id).select_related(
            "source_rfq_line", "product"
        )

    @classmethod
    def approval_decisions(cls, quotation_id):
        cls.quotation(quotation_id)
        return SalesQuotationApprovalDecision.objects.filter(
            quotation_id=quotation_id
        ).select_related("reviewer")

    @classmethod
    def customer_decisions(cls, quotation_id):
        cls.quotation(quotation_id)
        return SalesQuotationCustomerDecision.objects.filter(
            quotation_id=quotation_id
        ).select_related("recorded_by")

    @staticmethod
    def orders():
        return TransactionOrder.objects.select_related(
            "customer",
            "source_quotation",
            "source_rfq",
            "assigned_to",
            "created_by",
            "updated_by",
        )

    @classmethod
    def order(cls, object_id):
        return cls.orders().get(pk=object_id)

    @classmethod
    def order_lines(cls, order_id):
        cls.order(order_id)
        return TransactionOrderItem.objects.filter(order_id=order_id).select_related(
            "product", "source_quotation_line"
        )

    @classmethod
    def order_progress(cls, order_id):
        cls.order(order_id)
        return OrderProgressEvent.objects.filter(order_id=order_id).select_related("actor")

    @classmethod
    def entity_exists(cls, entity_type, entity_id):
        model = cls.ENTITY_MODELS.get(entity_type)
        return bool(model and model.objects.filter(pk=entity_id).exists())

    @classmethod
    def entity_audit_events(cls, entity_type, entity_id):
        if not cls.entity_exists(entity_type, entity_id):
            model = cls.ENTITY_MODELS.get(entity_type)
            if model is None:
                raise ValueError("Unsupported entity type.")
            raise model.DoesNotExist
        return AuditEvent.objects.filter(
            entity_type=entity_type,
            entity_id=str(entity_id),
        ).select_related("actor_user")

    @staticmethod
    def audit_events():
        return AuditEvent.objects.select_related("actor_user")
