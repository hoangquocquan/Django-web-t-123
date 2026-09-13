"""Authenticated read-only Phase 4A canonical API views."""

from rest_framework import status

from apps.api.canonical_contract import (
    CanonicalApiError,
    CanonicalAPIView,
    FilterSpec,
    boolean_filter,
    integer_filter,
    paginated_data,
    string_filter,
    success,
)
from apps.api.canonical_permissions import (
    ENTITY_PERMISSION_CODES,
    CanonicalReadPermission,
)
from apps.api.serializers.canonical import (
    approval_decision_to_dict,
    audit_event_to_dict,
    customer_decision_to_dict,
    customer_to_dict,
    material_to_dict,
    order_line_to_dict,
    order_to_dict,
    part_to_dict,
    progress_event_to_dict,
    quotation_family_to_dict,
    quotation_line_to_dict,
    quotation_summary_to_dict,
    quotation_to_dict,
    rfq_document_to_dict,
    rfq_line_to_dict,
    rfq_to_dict,
    technical_review_to_dict,
)
from apps.api.services.canonical_read_service import CanonicalReadService


DATA_CONTRACT_FILTER = {"data_contract": FilterSpec("data_contract", string_filter)}


class CanonicalResourceView(CanonicalAPIView):
    """Apply the canonical Phase 3 RBAC boundary to one API resource."""

    permission_classes = [CanonicalReadPermission]
    permission_code = ""

    def get_permission_code(self):
        return self.permission_code


class CanonicalListView(CanonicalResourceView):
    """Generic bounded list for an explicitly configured queryset and serializer."""

    serializer = None
    filters = {}
    ordering = {"id": "id"}
    default_ordering = ("id",)

    def get_queryset(self, **kwargs):
        raise NotImplementedError

    def get(self, request, **kwargs):
        return success(
            paginated_data(
                request,
                self.get_queryset(**kwargs),
                self.serializer,
                filters=self.filters,
                ordering=self.ordering,
                default_ordering=self.default_ordering,
            )
        )


class CustomerListView(CanonicalListView):
    permission_code = "customer:view"
    resource_name = "Customer"
    serializer = staticmethod(customer_to_dict)
    filters = {
        **DATA_CONTRACT_FILTER,
        "status": FilterSpec("status", string_filter),
        "country": FilterSpec("country", string_filter),
    }
    ordering = {
        "id": "id",
        "customer_code": "customer_code",
        "company_name": "company_name",
        "created_at": "created_at",
    }
    default_ordering = ("company_name", "id")

    def get_queryset(self, **kwargs):
        return CanonicalReadService.customers()


class CustomerDetailView(CanonicalResourceView):
    permission_code = "customer:view"
    resource_name = "Customer"

    def get(self, request, object_id):
        return success(customer_to_dict(CanonicalReadService.customer(object_id)))


class PartListView(CanonicalListView):
    permission_code = "part:view"
    resource_name = "Part"
    serializer = staticmethod(part_to_dict)
    filters = {
        **DATA_CONTRACT_FILTER,
        "is_active": FilterSpec("is_active", boolean_filter),
        "unit": FilterSpec("unit", string_filter),
        "material_id": FilterSpec("default_material_id", integer_filter),
    }
    ordering = {
        "id": "id",
        "part_code": "part_code",
        "name": "name",
        "created_at": "created_at",
    }
    default_ordering = ("part_code", "id")

    def get_queryset(self, **kwargs):
        return CanonicalReadService.parts()


class PartDetailView(CanonicalResourceView):
    permission_code = "part:view"
    resource_name = "Part"

    def get(self, request, object_id):
        return success(part_to_dict(CanonicalReadService.part(object_id)))


class MaterialListView(CanonicalListView):
    permission_code = "material:view"
    resource_name = "Material"
    serializer = staticmethod(material_to_dict)
    filters = {
        **DATA_CONTRACT_FILTER,
        "is_active": FilterSpec("is_active", boolean_filter),
    }
    ordering = {
        "id": "id",
        "material_code": "material_code",
        "name": "name",
        "created_at": "created_at",
    }
    default_ordering = ("material_code", "id")

    def get_queryset(self, **kwargs):
        return CanonicalReadService.materials()


class MaterialDetailView(CanonicalResourceView):
    permission_code = "material:view"
    resource_name = "Material"

    def get(self, request, object_id):
        return success(material_to_dict(CanonicalReadService.material(object_id)))


class RfqListView(CanonicalListView):
    permission_code = "rfq:view"
    resource_name = "RFQ"
    serializer = staticmethod(rfq_to_dict)
    filters = {
        **DATA_CONTRACT_FILTER,
        "status": FilterSpec("status", string_filter),
        "customer_id": FilterSpec("customer_id", integer_filter),
        "assigned_to_id": FilterSpec("assigned_to_id", integer_filter),
        "created_by_id": FilterSpec("created_by_id", integer_filter),
    }
    ordering = {
        "id": "id",
        "rfq_number": "rfq_number",
        "status": "status",
        "quote_due_at": "quote_due_at",
        "created_at": "created_at",
    }
    default_ordering = ("-created_at", "-id")

    def get_queryset(self, **kwargs):
        return CanonicalReadService.rfqs()


class RfqDetailView(CanonicalResourceView):
    permission_code = "rfq:view"
    resource_name = "RFQ"

    def get(self, request, rfq_id):
        return success(rfq_to_dict(CanonicalReadService.rfq(rfq_id)))


class RfqLineListView(CanonicalListView):
    permission_code = "rfq:view"
    resource_name = "RFQ"
    serializer = staticmethod(rfq_line_to_dict)
    ordering = {"id": "id", "line_number": "line_number"}
    default_ordering = ("line_number", "id")

    def get_queryset(self, rfq_id, **kwargs):
        return CanonicalReadService.rfq_lines(rfq_id)


class RfqDocumentListView(CanonicalListView):
    permission_code = "rfq:view"
    resource_name = "RFQ"
    serializer = staticmethod(rfq_document_to_dict)
    filters = {
        "rfq_line_id": FilterSpec("rfq_line_id", integer_filter),
        "mime_type": FilterSpec("mime_type", string_filter),
    }
    ordering = {"id": "id", "version": "version", "uploaded_at": "uploaded_at"}
    default_ordering = ("document_group_id", "version", "id")

    def get_queryset(self, rfq_id, **kwargs):
        return CanonicalReadService.rfq_documents(rfq_id)


class TechnicalReviewListView(CanonicalListView):
    permission_code = "rfq:view"
    resource_name = "RFQ"
    serializer = staticmethod(technical_review_to_dict)
    filters = {
        "decision": FilterSpec("decision", string_filter),
        "reviewer_id": FilterSpec("reviewer_id", integer_filter),
    }
    ordering = {"id": "id", "created_at": "created_at"}
    default_ordering = ("created_at", "id")

    def get_queryset(self, rfq_id, **kwargs):
        return CanonicalReadService.technical_reviews(rfq_id)


class QuotationFamilyListView(CanonicalListView):
    permission_code = "quotation:view"
    resource_name = "Quotation family"
    serializer = staticmethod(quotation_family_to_dict)
    filters = {
        "rfq_id": FilterSpec("id", integer_filter),
        "customer_id": FilterSpec("customer_id", integer_filter),
    }
    ordering = {
        "rfq_id": "id",
        "quotation_family_number": "quotation_family_number",
        "created_at": "created_at",
    }
    default_ordering = ("quotation_family_number", "id")

    def get_queryset(self, **kwargs):
        return CanonicalReadService.quotation_families()


class QuotationFamilyDetailView(CanonicalResourceView):
    permission_code = "quotation:view"
    resource_name = "Quotation family"

    def get(self, request, family_number):
        return success(
            quotation_family_to_dict(CanonicalReadService.quotation_family(family_number))
        )


class QuotationRevisionListView(CanonicalListView):
    permission_code = "quotation:view"
    resource_name = "Quotation family"
    serializer = staticmethod(quotation_summary_to_dict)
    filters = {
        **DATA_CONTRACT_FILTER,
        "workflow_status": FilterSpec("workflow_status", string_filter),
        "currency": FilterSpec("currency", string_filter),
    }
    ordering = {
        "id": "id",
        "revision": "revision",
        "valid_until": "valid_until",
        "created_at": "created_at",
    }
    default_ordering = ("revision", "id")

    def get_queryset(self, family_number, **kwargs):
        return CanonicalReadService.quotation_revisions(family_number)


class QuotationListView(CanonicalListView):
    permission_code = "quotation:view"
    resource_name = "Quotation"
    serializer = staticmethod(quotation_summary_to_dict)
    filters = {
        **DATA_CONTRACT_FILTER,
        "workflow_status": FilterSpec("workflow_status", string_filter),
        "currency": FilterSpec("currency", string_filter),
        "rfq_id": FilterSpec("rfq_id", integer_filter),
        "customer_id": FilterSpec("customer_id", integer_filter),
    }
    ordering = {
        "id": "id",
        "quotation_number": "quotation_number",
        "revision": "revision",
        "valid_until": "valid_until",
        "created_at": "created_at",
        "total": "total",
    }
    default_ordering = ("-created_at", "-id")

    def get_queryset(self, **kwargs):
        return CanonicalReadService.quotations()


class QuotationDetailView(CanonicalResourceView):
    permission_code = "quotation:view"
    resource_name = "Quotation"

    def get(self, request, quotation_id):
        return success(quotation_to_dict(CanonicalReadService.quotation(quotation_id)))


class QuotationLineListView(CanonicalListView):
    permission_code = "quotation:view"
    resource_name = "Quotation"
    serializer = staticmethod(quotation_line_to_dict)
    ordering = {"id": "id", "line_number": "line_number"}
    default_ordering = ("line_number", "id")

    def get_queryset(self, quotation_id, **kwargs):
        return CanonicalReadService.quotation_lines(quotation_id)


class ApprovalDecisionListView(CanonicalListView):
    permission_code = "quotation:view"
    resource_name = "Quotation"
    serializer = staticmethod(approval_decision_to_dict)
    ordering = {"id": "id", "decided_at": "decided_at"}
    default_ordering = ("decided_at", "id")

    def get_queryset(self, quotation_id, **kwargs):
        return CanonicalReadService.approval_decisions(quotation_id)


class CustomerDecisionListView(CanonicalListView):
    permission_code = "quotation:view"
    resource_name = "Quotation"
    serializer = staticmethod(customer_decision_to_dict)
    ordering = {"id": "id", "decided_at": "decided_at"}
    default_ordering = ("decided_at", "id")

    def get_queryset(self, quotation_id, **kwargs):
        return CanonicalReadService.customer_decisions(quotation_id)


class OrderListView(CanonicalListView):
    permission_code = "order:view"
    resource_name = "Sales order"
    serializer = staticmethod(order_to_dict)
    filters = {
        **DATA_CONTRACT_FILTER,
        "workflow_status": FilterSpec("workflow_status", string_filter),
        "currency": FilterSpec("currency", string_filter),
        "customer_id": FilterSpec("customer_id", integer_filter),
        "source_rfq_id": FilterSpec("source_rfq_id", integer_filter),
    }
    ordering = {
        "id": "id",
        "order_number": "order_number",
        "workflow_status": "workflow_status",
        "ordered_at": "ordered_at",
        "expected_delivery_date": "expected_delivery_date",
        "total_amount": "total_amount",
    }
    default_ordering = ("-ordered_at", "-id")

    def get_queryset(self, **kwargs):
        return CanonicalReadService.orders()


class OrderDetailView(CanonicalResourceView):
    permission_code = "order:view"
    resource_name = "Sales order"

    def get(self, request, order_id):
        return success(order_to_dict(CanonicalReadService.order(order_id)))


class OrderLineListView(CanonicalListView):
    permission_code = "order:view"
    resource_name = "Sales order"
    serializer = staticmethod(order_line_to_dict)
    ordering = {"id": "id", "line_number": "line_number"}
    default_ordering = ("line_number", "id")

    def get_queryset(self, order_id, **kwargs):
        return CanonicalReadService.order_lines(order_id)


class OrderProgressListView(CanonicalListView):
    permission_code = "order:view"
    resource_name = "Sales order"
    serializer = staticmethod(progress_event_to_dict)
    filters = {"to_status": FilterSpec("to_status", string_filter)}
    ordering = {"id": "id", "created_at": "created_at"}
    default_ordering = ("created_at", "id")

    def get_queryset(self, order_id, **kwargs):
        return CanonicalReadService.order_progress(order_id)


class EntityAuditTimelineView(CanonicalListView):
    resource_name = "Entity"
    serializer = staticmethod(audit_event_to_dict)
    filters = {"action": FilterSpec("action", string_filter)}
    ordering = {"id": "id", "created_at": "created_at"}
    default_ordering = ("created_at", "id")

    def get_permission_code(self):
        entity_type = self.kwargs.get("entity_type")
        try:
            return ENTITY_PERMISSION_CODES[entity_type]
        except KeyError as exc:
            raise CanonicalApiError(
                "unsupported_entity_type",
                "Unsupported entity timeline type.",
                status_code=status.HTTP_400_BAD_REQUEST,
            ) from exc

    def get_queryset(self, entity_type, entity_id, **kwargs):
        return CanonicalReadService.entity_audit_events(entity_type, entity_id)


class GlobalAuditListView(CanonicalListView):
    permission_code = "audit:view"
    resource_name = "Audit event"
    serializer = staticmethod(audit_event_to_dict)
    filters = {
        "entity_type": FilterSpec("entity_type", string_filter),
        "entity_id": FilterSpec("entity_id", string_filter),
        "action": FilterSpec("action", string_filter),
        "actor_ref": FilterSpec("actor_ref", string_filter),
    }
    ordering = {"id": "id", "created_at": "created_at"}
    default_ordering = ("-created_at", "-id")

    def get_queryset(self, **kwargs):
        return CanonicalReadService.audit_events()
