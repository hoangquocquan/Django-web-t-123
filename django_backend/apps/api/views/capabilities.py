"""Authenticated Capability CMS and anonymous published Capability API."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.api.serializers.capabilities import (
    CapabilityAdminSerializer,
    PublicCapabilitySerializer,
)
from apps.api.views.helpers import handle_not_found, ok, paginated_ok
from apps.business_core.capabilities import CapabilityPublicationService
from apps.foundation.services import FoundationAuthService

TRANSITION_PERMISSIONS = {
    ("DRAFT", "REVIEW"): "edit",
    ("REVIEW", "APPROVED"): "approve",
    ("APPROVED", "PUBLISHED"): "publish",
    ("PUBLISHED", "ARCHIVED"): "archive",
}


def _error(code, message, http_status):
    return Response(
        {"success": False, "error": {"code": code, "message": message}},
        status=http_status,
    )


def _authenticated_user(request):
    return FoundationAuthService().user_from_authorization_header(
        request.META.get("HTTP_AUTHORIZATION", "")
    )


def _require_exact_permission(user, action):
    role = getattr(user, "role", None)
    code = f"capabilities:{action}"
    if (
        not user.is_active
        or role is None
        or not role.is_active
        or not role.permissions.filter(
            code=code,
            module="capabilities",
            action=action,
        ).exists()
    ):
        raise PermissionDenied(f"Missing exact permission: {code}")


def _validation_error(exc):
    return _error(
        "validation_error",
        "; ".join(exc.messages),
        status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET", "POST"])
def admin_capabilities(request):
    """List Capability content or create a new DRAFT."""

    try:
        user = _authenticated_user(request)
        _require_exact_permission(user, "edit" if request.method == "POST" else "read")
    except PermissionDenied as exc:
        return _error("permission_denied", str(exc), status.HTTP_403_FORBIDDEN)

    service = CapabilityPublicationService()
    if request.method == "GET":
        queryset = service.list_all()
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(slug__icontains=search)
                | Q(technology_type__icontains=search)
                | Q(process_category__icontains=search)
            )
        requested_status = request.query_params.get("status", "").strip()
        if requested_status:
            queryset = queryset.filter(status=requested_status)
        ordering = request.query_params.get("ordering", "").strip()
        allowed_ordering = {
            "display_order",
            "-display_order",
            "title",
            "-title",
            "created_at",
            "-created_at",
        }
        if ordering in allowed_ordering:
            queryset = queryset.order_by(ordering, "id")
        return paginated_ok(
            request,
            queryset,
            lambda capability: CapabilityAdminSerializer(capability).data,
        )

    serializer = CapabilityAdminSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        capability = service.create(actor=user, **serializer.validated_data)
    except ValidationError as exc:
        return _validation_error(exc)
    return Response(
        {"success": True, "data": CapabilityAdminSerializer(capability).data},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PUT", "PATCH"])
def admin_capability_detail(request, capability_id):
    """Read, edit or transition one Capability under exact permissions."""

    try:
        user = _authenticated_user(request)
        if request.method == "GET":
            _require_exact_permission(user, "read")
    except PermissionDenied as exc:
        return _error("permission_denied", str(exc), status.HTTP_403_FORBIDDEN)

    def execute():
        service = CapabilityPublicationService()
        capability = service.get(capability_id)
        if request.method == "GET":
            return ok(CapabilityAdminSerializer(capability).data)

        requested_status = request.data.get("status")
        content_fields = set(request.data) - {"status"}
        try:
            if content_fields:
                _require_exact_permission(user, "edit")
            if requested_status and requested_status != capability.status:
                action = TRANSITION_PERMISSIONS.get(
                    (capability.status, requested_status)
                )
                if action is None:
                    return _error(
                        "validation_error",
                        f"Invalid capability transition: {capability.status} -> {requested_status}.",
                        status.HTTP_400_BAD_REQUEST,
                    )
                _require_exact_permission(user, action)
            if not content_fields and not requested_status:
                _require_exact_permission(user, "edit")
        except PermissionDenied as exc:
            return _error("permission_denied", str(exc), status.HTTP_403_FORBIDDEN)

        serializer = CapabilityAdminSerializer(
            capability,
            data=request.data,
            partial=request.method == "PATCH",
        )
        serializer.is_valid(raise_exception=True)
        try:
            updated = service.update(
                capability,
                actor=user,
                **serializer.validated_data,
            )
        except ValidationError as exc:
            return _validation_error(exc)
        return ok(CapabilityAdminSerializer(updated).data)

    return handle_not_found("Capability", execute)


@api_view(["GET"])
@permission_classes([AllowAny])
def public_capabilities(request):
    """Return active, effective PUBLISHED capabilities through an allowlist."""

    return paginated_ok(
        request,
        CapabilityPublicationService().list_published(),
        lambda capability: PublicCapabilitySerializer(capability).data,
    )


