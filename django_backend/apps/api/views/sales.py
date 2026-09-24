"""Sales quotation API views for migrated read and quote replacement contracts."""

from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.api.permissions import ReadOnlyApiPermission
from apps.api.serializers.sales import (
    quote_detail_to_dict,
    quote_file_to_dict,
    quote_to_dict,
    sales_lead_to_dict,
    sales_opportunity_to_dict,
    sales_quotation_to_dict,
)
from apps.api.views.helpers import created, handle_not_found, ok, paginated_ok
from apps.api.views.replacement import quote_create
from apps.foundation.services import FoundationAuthService, FoundationPermissionService
from apps.sales.models import SalesLead, SalesOpportunity, SalesQuotation
from apps.sales.services.sales_platform_service import SalesPlatformService
from apps.sales.services.quotation_service import QuotationService


class LeadCreateSerializer(serializers.Serializer):
    """Validate sales lead creation."""

    lead_source = serializers.CharField(required=False, allow_blank=True)
    company = serializers.CharField(max_length=220)
    contact_person = serializers.CharField(max_length=160)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    industry = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, default="new")
    priority = serializers.CharField(required=False, default="medium")
    notes = serializers.CharField(required=False, allow_blank=True)


class LeadTransitionSerializer(serializers.Serializer):
    """Validate lead pipeline movement."""

    status = serializers.CharField(max_length=40)


class OpportunityCreateSerializer(serializers.Serializer):
    """Validate opportunity creation."""

    lead_id = serializers.IntegerField(required=False)
    customer_id = serializers.IntegerField(required=False)
    title = serializers.CharField(max_length=220)
    value = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)
    probability = serializers.IntegerField(required=False, min_value=0, max_value=100)
    expected_close_date = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, default="open")
    notes = serializers.CharField(required=False, allow_blank=True)


class QuotationLineSerializer(serializers.Serializer):
    """Validate one managed quotation line."""

    product_id = serializers.IntegerField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)


class QuotationCreateSerializer(serializers.Serializer):
    """Validate managed quotation creation."""

    opportunity_id = serializers.IntegerField(required=False)
    customer_id = serializers.IntegerField(required=False)
    quotation_number = serializers.CharField(required=False, allow_blank=True)
    version = serializers.IntegerField(required=False, min_value=1)
    status = serializers.CharField(required=False, default="draft")
    approval_status = serializers.CharField(required=False, default="pending")
    lines = QuotationLineSerializer(many=True, required=False)


def _authorization_header(request):
    """Read the Bearer token header."""
    return request.META.get("HTTP_AUTHORIZATION", "")


def _permission_error_response(exc):
    """Return a consistent permission error."""
    return Response(
        {"success": False, "error": {"code": "permission_denied", "message": str(exc)}},
        status=status.HTTP_403_FORBIDDEN,
    )


def _require_sales_user(request, action="read"):
    """Authenticate and require sales permission."""
    user = FoundationAuthService().user_from_authorization_header(_authorization_header(request))
    FoundationPermissionService().require_permission(user, "sales", action)
    return user


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def quotes(request):
    """Return quote request headers or accept a public quote replacement intent."""
    if request.method == "POST":
        return quote_create(request)
    service = QuotationService()
    return paginated_ok(request, service.list_quotes(), quote_to_dict)


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def quote_detail(request, quote_id):
    """Return one quote with items and files through the Sales service layer."""
    service = QuotationService()
    return handle_not_found(
        "Quote",
        lambda: ok(quote_detail_to_dict(service.get_quote_detail(quote_id))),
    )


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def quote_files(request, quote_id):
    """Return quote file metadata without changing physical files."""
    service = QuotationService()
    return paginated_ok(request, service.list_quote_files(quote_id), quote_file_to_dict)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def sales_leads(request):
    """List or create professional sales leads."""
    action = "write" if request.method == "POST" else "read"
    try:
        user = _require_sales_user(request, action)
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    service = SalesPlatformService()
    if request.method == "GET":
        return paginated_ok(request, service.list_leads(), sales_lead_to_dict)

    serializer = LeadCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    lead = service.create_lead(serializer.validated_data, owner=user)
    return created(sales_lead_to_dict(lead))


@api_view(["POST"])
@permission_classes([AllowAny])
def sales_lead_transition(request, lead_id):
    """Move a lead through the sales pipeline."""
    try:
        user = _require_sales_user(request, "write")
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    serializer = LeadTransitionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        lead = SalesPlatformService().advance_lead(
            lead_id,
            serializer.validated_data["status"],
            actor=user.email,
        )
    except (SalesLead.DoesNotExist, ValidationError):
        return Response(
            {"success": False, "error": {"code": "invalid_transition", "message": "Lead transition failed."}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return ok(sales_lead_to_dict(lead))


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def sales_opportunities(request):
    """List or create sales opportunities."""
    action = "write" if request.method == "POST" else "read"
    try:
        user = _require_sales_user(request, action)
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    service = SalesPlatformService()
    if request.method == "GET":
        return paginated_ok(request, service.list_opportunities(), sales_opportunity_to_dict)

    serializer = OpportunityCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    opportunity = service.create_opportunity(serializer.validated_data, owner=user)
    return created(sales_opportunity_to_dict(opportunity))


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def sales_quotations(request):
    """List or create managed professional quotations."""
    action = "write" if request.method == "POST" else "read"
    try:
        user = _require_sales_user(request, action)
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    service = SalesPlatformService()
    if request.method == "GET":
        return paginated_ok(request, service.list_quotations(), sales_quotation_to_dict)

    serializer = QuotationCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    quotation = service.create_quotation(serializer.validated_data, user=user)
    return created(sales_quotation_to_dict(quotation))


@api_view(["GET"])
@permission_classes([AllowAny])
def sales_dashboard(request):
    """Return professional sales dashboard metrics."""
    try:
        _require_sales_user(request, "read")
    except PermissionDenied as exc:
        return _permission_error_response(exc)
    return ok(SalesPlatformService().dashboard())
