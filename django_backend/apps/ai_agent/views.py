"""API views for the local AI agent system."""

from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.ai_agent.services.agent_controller import AgentController
from apps.ai_agent.services.sales_assistant import SalesAssistantService
from apps.api.views.helpers import ok
from apps.ai.services.governance_service import AIGovernanceError, AIGovernanceService
from apps.foundation.services import FoundationAuthService, FoundationPermissionService


class AgentRunSerializer(serializers.Serializer):
    """Validate an agent execution request."""

    request = serializers.CharField(max_length=2000, allow_blank=False, trim_whitespace=True)


class SalesAssistantSerializer(serializers.Serializer):
    """Validate a safe AI Sales Assistant request."""

    action = serializers.ChoiceField(
        choices=["lead_analysis", "customer_summary", "email_draft", "weekly_recommendation"]
    )
    payload = serializers.DictField(required=False, default=dict)


def _authorization_header(request):
    """Read the Bearer token from the incoming request."""
    return request.META.get("HTTP_AUTHORIZATION", "")


def _permission_error_response(exc):
    """Return a consistent permission error payload."""
    return Response(
        {
            "success": False,
            "error": {
                "code": "permission_denied",
                "message": str(exc),
            },
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def _require_agent_user(request):
    """Authenticate and enforce agent write permission."""
    user = FoundationAuthService().user_from_authorization_header(_authorization_header(request))
    FoundationPermissionService().require_permission(user, "agent", "write")
    return user


def _require_ai_sales_user(request):
    """Authenticate and enforce AI sales read permission."""
    user = FoundationAuthService().user_from_authorization_header(_authorization_header(request))
    FoundationPermissionService().require_permission(user, "ai_sales", "read")
    return user


def _validation_error_response(exc):
    """Return validation errors without exposing stack traces."""
    messages = getattr(exc, "messages", [str(exc)])
    return Response(
        {
            "success": False,
            "error": {
                "code": "validation_error",
                "message": "; ".join(str(message) for message in messages),
            },
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def _governance_error_response(exc):
    """Return a consistent AI governance error payload."""
    return Response(
        {
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
            },
        },
        status=exc.status_code,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def agent_run(request):
    """Run the local tool-using AI agent."""
    try:
        user = _require_agent_user(request)
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    serializer = AgentRunSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    request_text = serializer.validated_data["request"]
    try:
        AIGovernanceService().enforce(
            user=user,
            endpoint="agent/run",
            action="agent_run",
            text=request_text,
        )
    except AIGovernanceError as exc:
        return _governance_error_response(exc)

    result = AgentController().run(request_text, user=user)
    return ok(result)


@api_view(["POST"])
@permission_classes([AllowAny])
def sales_assistant(request):
    """Run AI sales suggestions while keeping all business actions human-approved."""
    try:
        user = _require_ai_sales_user(request)
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    serializer = SalesAssistantSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data.get("payload", {})
    try:
        AIGovernanceService().enforce(
            user=user,
            endpoint="ai/sales-assistant",
            action=serializer.validated_data["action"],
            text=" ".join(str(value) for value in payload.values()),
            metadata={"action": serializer.validated_data["action"]},
        )
    except AIGovernanceError as exc:
        return _governance_error_response(exc)

    try:
        result = SalesAssistantService().handle(
            action=serializer.validated_data["action"],
            payload=payload,
            user=user,
        )
    except ValidationError as exc:
        return _validation_error_response(exc)
    except ObjectDoesNotExist:
        return Response(
            {
                "success": False,
                "error": {
                    "code": "not_found",
                    "message": "Requested sales or CRM record was not found.",
                },
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    return ok(result)
