"""CRM API views for migrated read and contact replacement contracts."""

from django.conf import settings
from django.core.exceptions import PermissionDenied
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.api.permissions import ReadOnlyApiPermission
from apps.api.serializers.crm import (
    business_customer_to_crm_dict,
    contact_request_to_dict,
    crm_customer_context_to_dict,
    crm_interaction_to_dict,
    customer_detail_to_dict,
    customer_to_dict,
)
from apps.api.views.helpers import created, handle_not_found, ok, paginated_ok
from apps.api.views.replacement import contact_create
from apps.crm.services.crm_platform_service import CrmPlatformService
from apps.crm.services.crm_service import CrmService
from apps.foundation.services import FoundationAuthService, FoundationPermissionService


class CrmCustomerCreateSerializer(serializers.Serializer):
    """Validate managed CRM customer creation."""

    company_name = serializers.CharField(required=False, allow_blank=True)
    contact_name = serializers.CharField(max_length=160)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True, default="Vietnam")
    status = serializers.CharField(required=False, default="lead")
    notes = serializers.CharField(required=False, allow_blank=True)
    segment = serializers.CharField(
        required=False, allow_blank=True, default="standard"
    )
    lifecycle_stage = serializers.CharField(required=False, default="lead")
    preferred_contact_method = serializers.CharField(required=False, allow_blank=True)
    summary = serializers.CharField(required=False, allow_blank=True)


class CrmInteractionCreateSerializer(serializers.Serializer):
    """Validate CRM interaction creation."""

    interaction_type = serializers.CharField(required=False, default="note")
    subject = serializers.CharField(max_length=220)
    content = serializers.CharField(required=False, allow_blank=True)
    occurred_at = serializers.CharField(required=False, allow_blank=True)


def _authorization_header(request):
    """Read the Bearer token header."""
    return request.META.get("HTTP_AUTHORIZATION", "")


def _permission_error_response(exc):
    """Return a consistent permission error."""
    return Response(
        {"success": False, "error": {"code": "permission_denied", "message": str(exc)}},
        status=status.HTTP_403_FORBIDDEN,
    )


def _legacy_fallback_blocked():
    """Do not query the retired legacy database in production-like runtimes."""
    return getattr(settings, "ENVIRONMENT", "development") in {"production", "staging"}


def _authentication_required_response():
    """Return a safe response before any unavailable legacy query is attempted."""
    return _permission_error_response(PermissionDenied("Authentication required."))


def _authenticated_user_or_none(request):
    """Return authenticated user when a Bearer token is present."""
    authorization = _authorization_header(request)
    if not authorization:
        return None
    return FoundationAuthService().user_from_authorization_header(authorization)


def _require_crm_user(request, action="read"):
    """Authenticate and require CRM permission."""
    user = FoundationAuthService().user_from_authorization_header(
        _authorization_header(request)
    )
    FoundationPermissionService().require_permission(user, "crm", action)
    return user


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def customers(request):
    """Return legacy or managed CRM customers, or create managed CRM customer."""
    if request.method == "POST":
        try:
            user = _require_crm_user(request, "write")
        except PermissionDenied as exc:
            return _permission_error_response(exc)
        serializer = CrmCustomerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = CrmPlatformService().create_customer(
            serializer.validated_data, owner=user
        )
        return created(business_customer_to_crm_dict(customer))

    try:
        user = _authenticated_user_or_none(request)
        if user:
            FoundationPermissionService().require_permission(user, "crm", "read")
            return paginated_ok(
                request,
                CrmPlatformService().list_customers(),
                business_customer_to_crm_dict,
            )
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    if _legacy_fallback_blocked():
        return _authentication_required_response()

    service = CrmService()
    return paginated_ok(request, service.list_customer_profiles(), customer_to_dict)


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def customer_detail(request, customer_id):
    """Return one customer with notes through the CRM service layer."""
    try:
        user = _authenticated_user_or_none(request)
        if user:
            FoundationPermissionService().require_permission(user, "crm", "read")
            return handle_not_found(
                "CRM customer",
                lambda: ok(
                    crm_customer_context_to_dict(
                        CrmPlatformService().get_customer_context(customer_id)
                    )
                ),
            )
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    if _legacy_fallback_blocked():
        return _authentication_required_response()

    service = CrmService()
    return handle_not_found(
        "Customer",
        lambda: ok(customer_detail_to_dict(service.get_customer_profile(customer_id))),
    )


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def contact_requests(request):
    """Return contact requests or accept a public contact replacement intent."""
    if request.method == "POST":
        return contact_create(request)
    if _legacy_fallback_blocked():
        return _authentication_required_response()
    service = CrmService()
    return paginated_ok(
        request, service.list_contact_requests(), contact_request_to_dict
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def crm_customer_interactions(request, customer_id):
    """Create an interaction on a managed CRM customer."""
    try:
        user = _require_crm_user(request, "write")
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    serializer = CrmInteractionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return handle_not_found(
        "CRM customer",
        lambda: created(
            crm_interaction_to_dict(
                CrmPlatformService().add_interaction(
                    customer_id, serializer.validated_data, actor=user.email
                )
            )
        ),
    )
