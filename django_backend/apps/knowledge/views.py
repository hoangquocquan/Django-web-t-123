"""API views for knowledge document management, search, and chat."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.api.views.helpers import created, ok
from apps.ai.services.governance_service import AIGovernanceError, AIGovernanceService
from apps.foundation.services import FoundationAuthService, FoundationPermissionService
from apps.knowledge.services.assistant_service import KnowledgeAssistantService
from apps.knowledge.services.document_processor import DocumentProcessor
from apps.knowledge.services.knowledge_service import KnowledgeService, document_to_dict
from apps.knowledge.services.search_service import KnowledgeSearchService


class KnowledgeDocumentSerializer(serializers.Serializer):
    """Validate document create requests."""

    title = serializers.CharField(max_length=240, allow_blank=False, trim_whitespace=True)
    description = serializers.CharField(required=False, allow_blank=True)
    content = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField(required=False, allow_blank=True, max_length=120)
    source_type = serializers.CharField(required=False, allow_blank=True, max_length=32, default="text")
    permission_level = serializers.ChoiceField(
        required=False,
        choices=["public", "internal", "restricted"],
        default="internal",
    )
    metadata = serializers.JSONField(required=False)


class KnowledgeSearchSerializer(serializers.Serializer):
    """Validate semantic search input."""

    query = serializers.CharField(max_length=1000, allow_blank=False, trim_whitespace=True)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=20, default=5)


class KnowledgeChatSerializer(serializers.Serializer):
    """Validate source-grounded assistant questions."""

    question = serializers.CharField(max_length=1200, allow_blank=False, trim_whitespace=True)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=10, default=5)


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


def _require_knowledge_user(request, action="read"):
    """Authenticate and enforce knowledge permission."""
    user = FoundationAuthService().user_from_authorization_header(_authorization_header(request))
    FoundationPermissionService().require_permission(user, "knowledge", action)
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


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def knowledge_documents(request):
    """List or create internal knowledge documents."""
    action = "write" if request.method == "POST" else "read"
    try:
        user = _require_knowledge_user(request, action)
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    service = KnowledgeService()
    if request.method == "GET":
        return ok([document_to_dict(document) for document in service.list_documents(user=user)])

    serializer = KnowledgeDocumentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    uploaded_file = request.FILES.get("file")
    if uploaded_file:
        processed = DocumentProcessor().process_uploaded_file(uploaded_file)
        content = processed["text"]
        source_type = processed["source_type"]
        source_path = processed["source_path"]
    else:
        content = data.get("content", "")
        source_type = data.get("source_type") or "text"
        source_path = ""

    document = service.create_document(
        title=data["title"],
        description=data.get("description", ""),
        category_name=data.get("category", ""),
        content=content,
        source_type=source_type,
        source_path=source_path,
        permission_level=data.get("permission_level", "internal"),
        created_by_email=user.email,
        metadata=data.get("metadata") or {},
    )
    return created(document_to_dict(document))


@api_view(["POST"])
@permission_classes([AllowAny])
def knowledge_search(request):
    """Search the local knowledge base and return relevant chunks."""
    try:
        user = _require_knowledge_user(request)
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    serializer = KnowledgeSearchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    query = serializer.validated_data["query"]
    try:
        AIGovernanceService().enforce(
            user=user,
            endpoint="knowledge/search",
            action="search",
            text=query,
            metadata={"limit": serializer.validated_data["limit"]},
        )
    except AIGovernanceError as exc:
        return _governance_error_response(exc)

    result = KnowledgeSearchService().search(
        query,
        limit=serializer.validated_data["limit"],
        user=user,
    )
    return ok(
        {
            "query": serializer.validated_data["query"],
            **result,
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def knowledge_chat(request):
    """Answer a question using retrieved knowledge and local Ollama."""
    try:
        user = _require_knowledge_user(request)
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    serializer = KnowledgeChatSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    question = serializer.validated_data["question"]
    try:
        AIGovernanceService().enforce(
            user=user,
            endpoint="knowledge/chat",
            action="chat",
            text=question,
            metadata={"limit": serializer.validated_data["limit"]},
        )
    except AIGovernanceError as exc:
        return _governance_error_response(exc)

    result = KnowledgeAssistantService().answer(
        question,
        user=user,
        limit=serializer.validated_data["limit"],
    )
    return ok(result)
