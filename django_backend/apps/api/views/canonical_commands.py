"""Explicit Phase 4B canonical command and RFQ document endpoints."""

from __future__ import annotations

from django.http import FileResponse
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from apps.api.canonical_contract import CanonicalAPIView, success
from apps.api.canonical_permissions import CanonicalCommandPermission
from apps.api.serializers.canonical import (
    approval_decision_to_dict,
    customer_decision_to_dict,
    customer_to_dict,
    material_to_dict,
    part_to_dict,
    order_to_dict,
    quotation_to_dict,
    rfq_document_to_dict,
    rfq_line_to_dict,
    rfq_to_dict,
    technical_review_to_dict,
)
from apps.api.serializers.canonical_commands import (
    CompleteReviewSerializer,
    CustomerCreateSerializer,
    CustomerUpdateSerializer,
    EmptyCommandSerializer,
    MaterialCreateSerializer,
    MaterialUpdateSerializer,
    OrderCompleteCommandSerializer,
    OrderProgressCommandSerializer,
    OrderReasonCommandSerializer,
    PartCreateSerializer,
    PartUpdateSerializer,
    QuotationApprovalSerializer,
    QuotationCreateSerializer,
    QuotationCustomerDecisionSerializer,
    QuotationRejectionSerializer,
    QuotationSendSerializer,
    QuotationUpdateSerializer,
    ReasonSerializer,
    RequestInformationSerializer,
    RfqCreateSerializer,
    RfqDocumentUploadSerializer,
    RfqLineCreateSerializer,
    RfqLineSerializer,
    RfqUpdateSerializer,
)
from apps.api.services.canonical_command_service import (
    MasterDataCommandService,
    OrderProgressCommandService,
    QuotationCommandService,
    RfqCommandService,
    RfqDocumentSecurityService,
)


class CanonicalCommandView(CanonicalAPIView):
    """Base class for one explicitly named POST command."""

    http_method_names = ["post", "options"]
    parser_classes = [JSONParser]
    permission_classes = [CanonicalCommandPermission]
    permission_code = ""
    visibility_permission_code = ""
    serializer_class = EmptyCommandSerializer

    def get_permission_code(self):
        return self.permission_code

    def get_visibility_permission_code(self):
        if self.visibility_permission_code:
            return self.visibility_permission_code
        return f"{self.get_permission_code().split(':', 1)[0]}:view"

    def validated(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data


class CustomerCreateCommandView(CanonicalCommandView):
    permission_code = "customer:create"
    serializer_class = CustomerCreateSerializer
    resource_name = "Customer"

    def post(self, request):
        customer = MasterDataCommandService.create_customer(
            request.user, self.validated(request)
        )
        return success(customer_to_dict(customer), status_code=status.HTTP_201_CREATED)


class CustomerUpdateCommandView(CanonicalCommandView):
    permission_code = "customer:change"
    serializer_class = CustomerUpdateSerializer
    resource_name = "Customer"

    def post(self, request, object_id):
        customer = MasterDataCommandService.update_customer(
            request.user, object_id, self.validated(request)
        )
        return success(customer_to_dict(customer))


class CustomerArchiveCommandView(CanonicalCommandView):
    permission_code = "customer:archive"
    resource_name = "Customer"

    def post(self, request, object_id):
        self.validated(request)
        customer = MasterDataCommandService.archive_customer(request.user, object_id)
        return success(customer_to_dict(customer))


class PartCreateCommandView(CanonicalCommandView):
    permission_code = "part:manage"
    serializer_class = PartCreateSerializer
    resource_name = "Part"

    def post(self, request):
        part = MasterDataCommandService.create_part(request.user, self.validated(request))
        return success(part_to_dict(part), status_code=status.HTTP_201_CREATED)


class PartUpdateCommandView(CanonicalCommandView):
    permission_code = "part:manage"
    serializer_class = PartUpdateSerializer
    resource_name = "Part"

    def post(self, request, object_id):
        part = MasterDataCommandService.update_part(
            request.user, object_id, self.validated(request)
        )
        return success(part_to_dict(part))


class PartArchiveCommandView(CanonicalCommandView):
    permission_code = "part:archive"
    resource_name = "Part"

    def post(self, request, object_id):
        self.validated(request)
        part = MasterDataCommandService.archive_part(request.user, object_id)
        return success(part_to_dict(part))


class MaterialCreateCommandView(CanonicalCommandView):
    permission_code = "material:manage"
    serializer_class = MaterialCreateSerializer
    resource_name = "Material"

    def post(self, request):
        material = MasterDataCommandService.create_material(
            request.user, self.validated(request)
        )
        return success(material_to_dict(material), status_code=status.HTTP_201_CREATED)


class MaterialUpdateCommandView(CanonicalCommandView):
    permission_code = "material:manage"
    serializer_class = MaterialUpdateSerializer
    resource_name = "Material"

    def post(self, request, object_id):
        material = MasterDataCommandService.update_material(
            request.user, object_id, self.validated(request)
        )
        return success(material_to_dict(material))


class MaterialArchiveCommandView(CanonicalCommandView):
    permission_code = "material:archive"
    resource_name = "Material"

    def post(self, request, object_id):
        self.validated(request)
        material = MasterDataCommandService.archive_material(request.user, object_id)
        return success(material_to_dict(material))


class RfqCreateCommandView(CanonicalCommandView):
    permission_code = "rfq:create"
    serializer_class = RfqCreateSerializer
    resource_name = "RFQ"

    def post(self, request):
        rfq, created = RfqCommandService.create(
            request.user,
            self.validated(request),
            request.headers.get("Idempotency-Key"),
        )
        return success(
            rfq_to_dict(rfq),
            status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class RfqUpdateCommandView(CanonicalCommandView):
    permission_code = "rfq:change"
    serializer_class = RfqUpdateSerializer
    resource_name = "RFQ"

    def post(self, request, rfq_id):
        rfq = RfqCommandService.update(request.user, rfq_id, self.validated(request))
        return success(rfq_to_dict(rfq))


class RfqLineAddCommandView(CanonicalCommandView):
    permission_code = "rfq:change"
    serializer_class = RfqLineCreateSerializer
    resource_name = "RFQ"

    def post(self, request, rfq_id):
        line = RfqCommandService.add_line(request.user, rfq_id, self.validated(request))
        return success(rfq_line_to_dict(line), status_code=status.HTTP_201_CREATED)


class RfqLineUpdateCommandView(CanonicalCommandView):
    permission_code = "rfq:change"
    serializer_class = RfqLineSerializer
    resource_name = "RFQ line"

    def post(self, request, rfq_id, line_id):
        line = RfqCommandService.update_line(
            request.user, rfq_id, line_id, self.validated(request)
        )
        return success(rfq_line_to_dict(line))


class RfqLineRemoveCommandView(CanonicalCommandView):
    permission_code = "rfq:change"
    resource_name = "RFQ line"

    def post(self, request, rfq_id, line_id):
        self.validated(request)
        RfqCommandService.remove_line(request.user, rfq_id, line_id)
        return success({"id": line_id, "removed": True})


class RfqSubmitCommandView(CanonicalCommandView):
    permission_code = "rfq:submit"
    resource_name = "RFQ"

    def post(self, request, rfq_id):
        self.validated(request)
        return success(rfq_to_dict(RfqCommandService.submit(request.user, rfq_id)))


class RfqArchiveCommandView(CanonicalCommandView):
    permission_code = "rfq:archive"
    serializer_class = ReasonSerializer
    resource_name = "RFQ"

    def post(self, request, rfq_id):
        data = self.validated(request)
        return success(
            rfq_to_dict(RfqCommandService.archive(request.user, rfq_id, data["reason"]))
        )


class RfqResubmitCommandView(CanonicalCommandView):
    permission_code = "rfq:submit"
    resource_name = "RFQ"

    def post(self, request, rfq_id):
        self.validated(request)
        return success(rfq_to_dict(RfqCommandService.resubmit(request.user, rfq_id)))


def _review_payload(rfq, review):
    return {"rfq": rfq_to_dict(rfq), "review": technical_review_to_dict(review)}


class RfqReviewStartCommandView(CanonicalCommandView):
    permission_code = "rfq:review"
    resource_name = "RFQ"

    def post(self, request, rfq_id):
        self.validated(request)
        return success(_review_payload(*RfqCommandService.start_review(request.user, rfq_id)))


class RfqRequestInformationCommandView(CanonicalCommandView):
    permission_code = "rfq:review"
    serializer_class = RequestInformationSerializer
    resource_name = "RFQ"

    def post(self, request, rfq_id):
        return success(
            _review_payload(
                *RfqCommandService.request_information(
                    request.user, rfq_id, self.validated(request)
                )
            )
        )


class RfqReviewCompleteCommandView(CanonicalCommandView):
    permission_code = "rfq:review"
    serializer_class = CompleteReviewSerializer
    resource_name = "RFQ"

    def post(self, request, rfq_id):
        return success(
            _review_payload(
                *RfqCommandService.complete_review(
                    request.user, rfq_id, self.validated(request)
                )
            )
        )


class RfqReviewDeclineCommandView(CanonicalCommandView):
    permission_code = "rfq:review"
    serializer_class = ReasonSerializer
    resource_name = "RFQ"

    def post(self, request, rfq_id):
        data = self.validated(request)
        return success(
            _review_payload(
                *RfqCommandService.decline(request.user, rfq_id, data["reason"])
            )
        )


class RfqAcknowledgeDeclinedCommandView(CanonicalCommandView):
    serializer_class = ReasonSerializer
    resource_name = "RFQ"

    def get_permission_code(self):
        role_name = getattr(getattr(self.request.user, "role", None), "name", None)
        return "rfq:review" if role_name == "Manager" else "rfq:archive"

    def post(self, request, rfq_id):
        data = self.validated(request)
        return success(
            rfq_to_dict(
                RfqCommandService.acknowledge_declined(
                    request.user, rfq_id, data["reason"]
                )
            )
        )


class QuotationCreateCommandView(CanonicalCommandView):
    permission_code = "quotation:create_revision"
    serializer_class = QuotationCreateSerializer
    resource_name = "Quotation"

    def post(self, request, rfq_id):
        quotation, created = QuotationCommandService.create(
            request.user,
            rfq_id,
            self.validated(request),
            request.headers.get("Idempotency-Key"),
        )
        return success(
            quotation_to_dict(quotation),
            status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class QuotationRevisionCreateCommandView(QuotationCreateCommandView):
    def post(self, request, quotation_id):
        source = QuotationCommandService.quotation_source(request.user, quotation_id)
        quotation, created = QuotationCommandService.create(
            request.user,
            source.rfq_id,
            self.validated(request),
            request.headers.get("Idempotency-Key"),
            source_quotation_id=source.pk,
        )
        return success(
            quotation_to_dict(quotation),
            status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class QuotationUpdateCommandView(CanonicalCommandView):
    permission_code = "quotation:change"
    serializer_class = QuotationUpdateSerializer
    resource_name = "Quotation"

    def post(self, request, quotation_id):
        quotation = QuotationCommandService.update(
            request.user, quotation_id, self.validated(request)
        )
        return success(quotation_to_dict(quotation))


class QuotationArchiveCommandView(CanonicalCommandView):
    permission_code = "quotation:archive"
    resource_name = "Quotation"

    def post(self, request, quotation_id):
        self.validated(request)
        return success(
            quotation_to_dict(
                QuotationCommandService.archive(request.user, quotation_id)
            )
        )


class QuotationSubmitCommandView(CanonicalCommandView):
    permission_code = "quotation:submit"
    resource_name = "Quotation"

    def post(self, request, quotation_id):
        self.validated(request)
        return success(
            quotation_to_dict(
                QuotationCommandService.submit(request.user, quotation_id)
            )
        )


class QuotationApproveCommandView(CanonicalCommandView):
    permission_code = "quotation:approve"
    serializer_class = QuotationApprovalSerializer
    resource_name = "Quotation"

    def post(self, request, quotation_id):
        data = self.validated(request)
        decision, quotation = QuotationCommandService.decide(
            request.user,
            quotation_id,
            decision="APPROVED",
            notes=data.get("notes", ""),
        )
        return success(
            {
                "quotation": quotation_to_dict(quotation),
                "decision": approval_decision_to_dict(decision),
            }
        )


class QuotationRejectCommandView(CanonicalCommandView):
    permission_code = "quotation:reject"
    serializer_class = QuotationRejectionSerializer
    resource_name = "Quotation"

    def post(self, request, quotation_id):
        data = self.validated(request)
        decision, quotation = QuotationCommandService.decide(
            request.user,
            quotation_id,
            decision="REJECTED",
            reason=data["reason"],
            notes=data.get("notes", ""),
        )
        return success(
            {
                "quotation": quotation_to_dict(quotation),
                "decision": approval_decision_to_dict(decision),
            }
        )


class QuotationSendCommandView(CanonicalCommandView):
    permission_code = "quotation:send"
    serializer_class = QuotationSendSerializer
    resource_name = "Quotation"

    def post(self, request, quotation_id):
        quotation = QuotationCommandService.send(
            request.user, quotation_id, self.validated(request)
        )
        return success(quotation_to_dict(quotation))


class QuotationCustomerDecisionCommandView(CanonicalCommandView):
    permission_code = "quotation:record_customer_decision"
    serializer_class = QuotationCustomerDecisionSerializer
    resource_name = "Quotation"
    decision = ""

    def post(self, request, quotation_id):
        decision, quotation = QuotationCommandService.record_customer_decision(
            request.user,
            quotation_id,
            self.validated(request),
            decision=self.decision,
        )
        return success(
            {
                "quotation": quotation_to_dict(quotation),
                "decision": customer_decision_to_dict(decision),
            }
        )


class QuotationAcceptCommandView(QuotationCustomerDecisionCommandView):
    decision = "ACCEPTED"


class QuotationDeclineCommandView(QuotationCustomerDecisionCommandView):
    decision = "DECLINED"


class QuotationConvertCommandView(CanonicalCommandView):
    permission_code = "quotation:convert"
    resource_name = "Quotation"

    def post(self, request, quotation_id):
        self.validated(request)
        order, created = QuotationCommandService.convert(
            request.user,
            quotation_id,
            request.headers.get("Idempotency-Key"),
        )
        return success(
            order_to_dict(order),
            status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class OrderProgressCommandView(CanonicalCommandView):
    permission_code = "order:progress"
    serializer_class = OrderProgressCommandSerializer
    resource_name = "Sales order"

    def post(self, request, order_id):
        order = OrderProgressCommandService.progress(
            request.user, order_id, self.validated(request)
        )
        return success(order_to_dict(order))


class OrderHoldCommandView(CanonicalCommandView):
    permission_code = "order:hold"
    serializer_class = OrderReasonCommandSerializer
    resource_name = "Sales order"

    def post(self, request, order_id):
        order = OrderProgressCommandService.hold(
            request.user, order_id, self.validated(request)
        )
        return success(order_to_dict(order))


class OrderResumeCommandView(CanonicalCommandView):
    permission_code = "order:resume"
    serializer_class = OrderProgressCommandSerializer
    resource_name = "Sales order"

    def post(self, request, order_id):
        order = OrderProgressCommandService.resume(
            request.user, order_id, self.validated(request)
        )
        return success(order_to_dict(order))


class OrderCompleteCommandView(CanonicalCommandView):
    permission_code = "order:complete"
    serializer_class = OrderCompleteCommandSerializer
    resource_name = "Sales order"

    def post(self, request, order_id):
        order = OrderProgressCommandService.complete(
            request.user, order_id, self.validated(request)
        )
        return success(order_to_dict(order))


class OrderCancelCommandView(CanonicalCommandView):
    permission_code = "order:cancel"
    serializer_class = OrderReasonCommandSerializer
    resource_name = "Sales order"

    def post(self, request, order_id):
        order = OrderProgressCommandService.cancel(
            request.user, order_id, self.validated(request)
        )
        return success(order_to_dict(order))


class RfqDocumentUploadCommandView(CanonicalCommandView):
    permission_code = "rfq:document_upload"
    serializer_class = RfqDocumentUploadSerializer
    resource_name = "RFQ"
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, rfq_id):
        document = RfqDocumentSecurityService().upload(
            request.user, rfq_id, self.validated(request)
        )
        return success(
            rfq_document_to_dict(document), status_code=status.HTTP_201_CREATED
        )


class RfqDocumentVersionCommandView(RfqDocumentUploadCommandView):
    def post(self, request, rfq_id, document_id):
        document = RfqDocumentSecurityService().upload(
            request.user,
            rfq_id,
            self.validated(request),
            replaces_id=document_id,
        )
        return success(
            rfq_document_to_dict(document), status_code=status.HTTP_201_CREATED
        )


class RfqDocumentDownloadView(CanonicalCommandView):
    http_method_names = ["get", "head", "options"]
    permission_code = "rfq:document_download"
    resource_name = "RFQ document"

    def get(self, request, rfq_id, document_id):
        document, stream = RfqDocumentSecurityService.open_for_download(
            request.user, rfq_id, document_id
        )
        return FileResponse(
            stream,
            as_attachment=True,
            filename=document.original_filename,
            content_type=document.mime_type,
        )
