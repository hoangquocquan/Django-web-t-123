"""Admin publication foundation and anonymous Public Product read API."""

from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.api.serializers.public_products import (
    PublicProductProjectionAdminSerializer,
    PublicProductSerializer,
)
from apps.api.views.helpers import handle_not_found, ok, paginated_ok
from apps.business_core.publication import PublicProductPublicationService
from apps.foundation.services import FoundationAuthService

TRANSITION_PERMISSIONS = {
    ("DRAFT", "REVIEW"): "edit",
    ("REVIEW", "DRAFT"): "review",
    ("REVIEW", "APPROVED"): "approve",
    ("APPROVED", "DRAFT"): "approve",
    ("APPROVED", "PUBLISHED"): "publish",
    ("PUBLISHED", "ARCHIVED"): "archive",
    ("ARCHIVED", "DRAFT"): "edit",
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
    code = f"public_products:{action}"
    if (
        not user.is_active
        or role is None
        or not role.is_active
        or not role.permissions.filter(
            code=code,
            module="public_products",
            action=action,
        ).exists()
    ):
        raise PermissionDenied(f"Missing exact permission: {code}")


def _transition_permission(current_status, target_status):
    return TRANSITION_PERMISSIONS.get((current_status, target_status), "edit")


@api_view(["GET", "POST"])
def admin_public_products(request):
    """List or create a DRAFT public projection using existing Product permissions."""

    try:
        user = _authenticated_user(request)
        _require_exact_permission(user, "edit" if request.method == "POST" else "read")
    except PermissionDenied as exc:
        return _error("permission_denied", str(exc), status.HTTP_403_FORBIDDEN)

    service = PublicProductPublicationService()
    if request.method == "GET":
        return paginated_ok(
            request,
            service.list_all(),
            lambda projection: PublicProductProjectionAdminSerializer(projection).data,
        )

    serializer = PublicProductProjectionAdminSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    fields = dict(serializer.validated_data)
    source_product = fields.pop("source_product")
    try:
        projection = service.create(source_product=source_product, actor=user, **fields)
    except ValidationError as exc:
        return _error("validation_error", "; ".join(exc.messages), status.HTTP_400_BAD_REQUEST)
    return Response(
        {"success": True, "data": PublicProductProjectionAdminSerializer(projection).data},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PUT"])
def admin_public_product_detail(request, projection_id):
    """Read or update content/state without mutating the source Product."""

    try:
        user = _authenticated_user(request)
        if request.method == "GET":
            _require_exact_permission(user, "read")
    except PermissionDenied as exc:
        return _error("permission_denied", str(exc), status.HTTP_403_FORBIDDEN)

    def execute():
        projection = PublicProductPublicationService().get(projection_id)
        if request.method == "GET":
            return ok(PublicProductProjectionAdminSerializer(projection).data)
        try:
            requested_status = request.data.get("publication_status")
            content_fields = set(request.data) - {"publication_status"}
            if content_fields:
                _require_exact_permission(user, "edit")
            if requested_status and requested_status != projection.publication_status:
                _require_exact_permission(
                    user,
                    _transition_permission(projection.publication_status, requested_status),
                )
            if not content_fields and not requested_status:
                _require_exact_permission(user, "edit")
        except PermissionDenied as exc:
            return _error("permission_denied", str(exc), status.HTTP_403_FORBIDDEN)
        serializer = PublicProductProjectionAdminSerializer(
            projection,
            data=request.data,
            partial=True,
        )
        serializer.fields["source_product_id"].read_only = True
        serializer.is_valid(raise_exception=True)
        try:
            updated = PublicProductPublicationService().update(
                projection, actor=user, **serializer.validated_data
            )
        except ValidationError as exc:
            return _error(
                "validation_error",
                "; ".join(exc.messages),
                status.HTTP_400_BAD_REQUEST,
            )
        return ok(PublicProductProjectionAdminSerializer(updated).data)

    return handle_not_found("Public product projection", execute)


@api_view(["GET"])
@permission_classes([AllowAny])
def public_products(request):
    """Return only effective PUBLISHED projections through a strict allowlist."""

    return paginated_ok(
        request,
        PublicProductPublicationService().list_published(),
        lambda projection: PublicProductSerializer(projection).data,
    )


