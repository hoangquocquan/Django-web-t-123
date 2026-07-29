"""API views for RAG knowledge search."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.api.views.helpers import ok
from apps.foundation.services import FoundationAuthService, FoundationPermissionService
from apps.knowledge.services.knowledge_service import KnowledgeService, search_result_to_dict


class KnowledgeSearchSerializer(serializers.Serializer):
    """Validate semantic search input."""

    query = serializers.CharField(max_length=1000, allow_blank=False, trim_whitespace=True)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=20, default=5)


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


def _require_knowledge_user(request):
    """Authenticate and enforce knowledge read permission."""
    user = FoundationAuthService().user_from_authorization_header(_authorization_header(request))
    FoundationPermissionService().require_permission(user, "knowledge", "read")
    return user


@api_view(["POST"])
@permission_classes([AllowAny])
def knowledge_search(request):
    """Search the local knowledge base and return relevant chunks."""
    try:
        _require_knowledge_user(request)
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    serializer = KnowledgeSearchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    results = KnowledgeService().search(
        serializer.validated_data["query"],
        limit=serializer.validated_data["limit"],
    )
    return ok(
        {
            "query": serializer.validated_data["query"],
            "results": [search_result_to_dict(result) for result in results],
        }
    )

