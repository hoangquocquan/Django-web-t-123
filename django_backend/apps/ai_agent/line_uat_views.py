"""Internal APIs for the synthetic n8n + LINE approval demo."""

from django.core.exceptions import PermissionDenied
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.ai_agent.models import OutboundMessageApproval
from apps.ai_agent.services.line_uat import (
    LineUATApprovalService,
    LineUATError,
    serialize_approval,
)
from apps.api.views.helpers import created, ok
from apps.foundation.services import FoundationAuthService, FoundationPermissionService


class StrictBooleanField(serializers.BooleanField):
    """Accept JSON booleans only; reject strings and numeric coercion."""

    def to_internal_value(self, data):
        if type(data) is not bool:
            raise serializers.ValidationError("Must be a JSON boolean.")
        return data


class StrictPayloadSerializer(serializers.Serializer):
    """Reject unknown fields rather than silently ignoring client input."""

    def validate(self, attrs):
        if set(self.initial_data) - set(self.fields):
            raise serializers.ValidationError("Unsupported request fields were provided.")
        return attrs


class EmptyPayloadSerializer(StrictPayloadSerializer):
    """Require an empty JSON object for state-changing actions without input."""


class UATDraftSerializer(StrictPayloadSerializer):
    rfq_id = serializers.CharField(max_length=80)
    synthetic = StrictBooleanField()
    environment = serializers.CharField(max_length=16)


class UATRejectSerializer(StrictPayloadSerializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)


def _authorization_header(request):
    return request.META.get("HTTP_AUTHORIZATION", "")


def _require_sales_user(request):
    user = FoundationAuthService().user_from_authorization_header(_authorization_header(request))
    role = str(getattr(getattr(user, "role", None), "name", "")).casefold()
    if role not in {"sales", "manager", "admin"}:
        raise PermissionDenied("This role is not authorized for the LINE UAT demo.")
    permissions = FoundationPermissionService()
    permissions.require_permission(user, "ai_sales", "read")
    permissions.require_permission(user, "sales", "read")
    permissions.require_permission(user, "line_uat", "read")
    return user


def _require_reviewer(request):
    user = _require_sales_user(request)
    role = str(user.role.name).casefold()
    if role not in {"manager", "admin"}:
        raise PermissionDenied("Only Manager or Admin may approve, reject, or send.")
    FoundationPermissionService().require_permission(user, "line_uat", "approve")
    return user


def _permission_error(exc):
    return Response(
        {"success": False, "error": {"code": "permission_denied", "message": str(exc)}},
        status=status.HTTP_403_FORBIDDEN,
    )


def _service_error(exc):
    http_status = status.HTTP_404_NOT_FOUND if exc.code == "not_found" else status.HTTP_409_CONFLICT
    if exc.code in {"synthetic_required", "uat_only", "unknown_uat_rfq"}:
        http_status = status.HTTP_400_BAD_REQUEST
    return Response(
        {"success": False, "error": {"code": exc.code, "message": exc.message}},
        status=http_status,
    )


def _approval(approval_id):
    try:
        return OutboundMessageApproval.objects.select_related(
            "approved_by", "rejected_by"
        ).get(pk=approval_id)
    except (OutboundMessageApproval.DoesNotExist, ValueError) as exc:
        raise LineUATError("not_found", "UAT LINE approval was not found.") from exc


@api_view(["POST"])
@permission_classes([AllowAny])
def line_uat_drafts(request):
    try:
        user = _require_sales_user(request)
    except PermissionDenied as exc:
        return _permission_error(exc)
    serializer = UATDraftSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        approval = LineUATApprovalService().create_draft(
            user=user, **serializer.validated_data
        )
    except LineUATError as exc:
        return _service_error(exc)
    return created(serialize_approval(approval))


@api_view(["GET"])
@permission_classes([AllowAny])
def line_uat_approval_detail(request, approval_id):
    try:
        _require_sales_user(request)
        approval = _approval(approval_id)
    except PermissionDenied as exc:
        return _permission_error(exc)
    except LineUATError as exc:
        return _service_error(exc)
    return ok(serialize_approval(approval))


@api_view(["POST"])
@permission_classes([AllowAny])
def line_uat_approve(request, approval_id):
    try:
        user = _require_reviewer(request)
        serializer = EmptyPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approval = LineUATApprovalService().approve(approval_id, user=user)
    except PermissionDenied as exc:
        return _permission_error(exc)
    except LineUATError as exc:
        return _service_error(exc)
    return ok(serialize_approval(approval))


@api_view(["POST"])
@permission_classes([AllowAny])
def line_uat_reject(request, approval_id):
    try:
        user = _require_reviewer(request)
    except PermissionDenied as exc:
        return _permission_error(exc)
    serializer = UATRejectSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        approval = LineUATApprovalService().reject(
            approval_id,
            user=user,
            reason=serializer.validated_data.get("reason", ""),
        )
    except LineUATError as exc:
        return _service_error(exc)
    return ok(serialize_approval(approval))


@api_view(["POST"])
@permission_classes([AllowAny])
def line_uat_send(request, approval_id):
    try:
        user = _require_reviewer(request)
        serializer = EmptyPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approval = LineUATApprovalService().send(approval_id, user=user)
    except PermissionDenied as exc:
        return _permission_error(exc)
    except LineUATError as exc:
        return _service_error(exc)
    return ok(serialize_approval(approval))
