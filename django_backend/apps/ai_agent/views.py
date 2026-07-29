"""API views for the local AI agent system."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.ai_agent.services.agent_controller import AgentController
from apps.api.views.helpers import ok
from apps.foundation.services import FoundationAuthService, FoundationPermissionService


class AgentRunSerializer(serializers.Serializer):
    """Validate an agent execution request."""

    request = serializers.CharField(max_length=2000, allow_blank=False, trim_whitespace=True)


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
    result = AgentController().run(serializer.validated_data["request"], user=user)
    return ok(result)

