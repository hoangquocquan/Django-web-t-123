"""API views for the Django-owned AI foundation layer."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.ai.services.health_service import OllamaHealthService
from apps.ai.services.governance_service import AIGovernanceError, AIGovernanceService
from apps.ai.services.ollama_client import OllamaClient, OllamaClientError
from apps.ai.services.prompt_manager import PromptManager
from apps.api.views.helpers import bad_request, ok
from apps.foundation.services import FoundationAuthService, FoundationPermissionService


class AiChatRequestSerializer(serializers.Serializer):
    """Validate the chat request body before a prompt is built."""

    message = serializers.CharField(max_length=2000, allow_blank=False, trim_whitespace=True)


def _authorization_header(request):
    """Read the Bearer token from the incoming request."""
    return request.META.get("HTTP_AUTHORIZATION", "")


def _permission_error_response(exc):
    """Return the existing project-style permission error payload."""
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


def _require_ai_user(request):
    """Authenticate the user and require AI write permission."""
    user = FoundationAuthService().user_from_authorization_header(_authorization_header(request))
    FoundationPermissionService().require_permission(user, "ai", "write")
    return user


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
def ai_chat(request):
    """Send one authenticated chat message to the local Ollama model."""
    try:
        user = _require_ai_user(request)
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    serializer = AiChatRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    message = serializer.validated_data["message"]

    try:
        AIGovernanceService().enforce(
            user=user,
            endpoint="ai/chat",
            action="chat",
            text=message,
        )
    except AIGovernanceError as exc:
        return _governance_error_response(exc)

    try:
        prompt = PromptManager().prepare_chat_prompt(message)
    except ValidationError as exc:
        return bad_request("validation_error", "; ".join(str(message) for message in exc.messages))

    try:
        ai_response = OllamaClient().generate_response(prompt.combined)
    except OllamaClientError as exc:
        return Response(
            {
                "success": False,
                "error": {
                    "code": "ollama_unavailable",
                    "message": str(exc),
                },
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return ok(
        {
            "answer": ai_response.answer,
            "model": ai_response.model,
            "provider": "ollama-local",
            "response_time_ms": ai_response.response_time_ms,
            "user": {
                "id": user.id,
                "email": user.email,
            },
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def ai_health(request):
    """Return local Ollama runtime health for monitoring screens."""
    return Response(OllamaHealthService().check())
