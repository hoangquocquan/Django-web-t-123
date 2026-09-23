"""API views for knowledge document management, search, and chat."""

from __future__ import annotations

from pathlib import PurePosixPath

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.storage import default_storage
from django.db.models import Q
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.ai.services.governance_service import AIGovernanceError, AIGovernanceService
from apps.api.views.helpers import created, ok
from apps.foundation.services import FoundationAuthService, FoundationPermissionService
from apps.knowledge.models import (
    KnowledgeAssistantFeedback, KnowledgeAssistantLog, KnowledgeAuditEvent,
    KnowledgeDocument, KnowledgeGapReview, KnowledgeHumanEvaluation,
    KnowledgeUserScope,
)
from apps.knowledge.services.assistant_service import KnowledgeAssistantService
from apps.knowledge.services.governance import KnowledgeGovernanceService
from apps.knowledge.services.document_processor import DocumentProcessor
from apps.knowledge.services.knowledge_service import KnowledgeService, document_to_dict
from apps.knowledge.services.pilot_monitoring import PilotMonitoringService
from apps.knowledge.services.pilot_governance import PilotGovernanceService
from apps.knowledge.services.pilot_program import PilotProgramService
from apps.knowledge.services.runtime_health import KnowledgeRuntimeHealthService
from apps.knowledge.services.search_service import KnowledgeSearchService
from apps.knowledge.services.synthetic_rag_demo import SyntheticRagWebDemoService
from apps.knowledge.services.upload_security import stored_file_cleanup


class KnowledgeDocumentSerializer(serializers.Serializer):
    """Validate document create requests."""

    title = serializers.CharField(
        max_length=240, allow_blank=False, trim_whitespace=True
    )
    description = serializers.CharField(required=False, allow_blank=True)
    content = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField(required=False, allow_blank=True, max_length=120)
    source_type = serializers.CharField(
        required=False, allow_blank=True, max_length=32, default="text"
    )
    permission_level = serializers.ChoiceField(
        required=False,
        choices=["public", "internal", "restricted"],
        default="internal",
    )
    department = serializers.ChoiceField(
        required=False,
        choices=["SALES", "ENGINEERING", "QC", "MANAGEMENT"],
        allow_blank=True,
        default="",
    )
    owner_email = serializers.EmailField(required=False, allow_blank=True)
    effective_date = serializers.DateField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False)


class KnowledgeSearchSerializer(serializers.Serializer):
    """Validate semantic search input."""

    query = serializers.CharField(
        max_length=1000, allow_blank=False, trim_whitespace=True
    )
    limit = serializers.IntegerField(
        required=False, min_value=1, max_value=20, default=5
    )


class KnowledgeChatSerializer(serializers.Serializer):
    """Validate source-grounded assistant questions."""

    question = serializers.CharField(
        max_length=1200, allow_blank=False, trim_whitespace=True
    )
    limit = serializers.IntegerField(
        required=False, min_value=1, max_value=10, default=5
    )








class KnowledgeFeedbackSerializer(serializers.Serializer):
    """Accept structured feedback without free-form answer content."""

    interaction_id = serializers.IntegerField(min_value=1)
    category = serializers.ChoiceField(
        choices=["HELPFUL", "INCORRECT", "MISSING_SOURCE", "NEED_DOCUMENT"]
    )


class KnowledgeHumanEvaluationSerializer(serializers.Serializer):
    """Validate a content-free human quality rating."""

    interaction_id = serializers.IntegerField(min_value=1)
    question_category = serializers.ChoiceField(
        choices=["PRODUCT", "CAPABILITY", "RFQ", "TECHNICAL", "QUALITY"]
    )
    rating = serializers.ChoiceField(
        choices=["CORRECT", "PARTIALLY_CORRECT", "INCORRECT"]
    )
    citation_valid = serializers.BooleanField()
    permission_correct = serializers.BooleanField()
    missing_information = serializers.BooleanField(default=False)
    hallucination = serializers.BooleanField(default=False)


class KnowledgeGapReviewSerializer(serializers.Serializer):
    """Validate a structured failed-answer root-cause classification."""

    interaction_id = serializers.IntegerField(min_value=1)
    category = serializers.ChoiceField(choices=[
        "MISSING_DOCUMENT", "POOR_DOCUMENT_QUALITY",
        "WRONG_DOCUMENT", "RETRIEVAL_ISSUE", "PERMISSION_ISSUE",
    ])
    resolved = serializers.BooleanField(default=False)


class KnowledgePilotLaunchSerializer(serializers.Serializer):
    """Validate the bounded 2–4 week pilot window."""

    planned_start = serializers.DateField()
    planned_end = serializers.DateField()


class KnowledgeQualityReviewSerializer(serializers.Serializer):
    """Validate a structured quality review without free-form sensitive notes."""

    decision = serializers.ChoiceField(choices=["APPROVED", "REJECTED"])
    rejection_reason = serializers.ChoiceField(
        required=False, allow_blank=True,
        choices=["", "INCOMPLETE", "OUTDATED", "CONFIDENTIAL", "INVALID_METADATA"],
        default="",
    )


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
    user = FoundationAuthService().user_from_authorization_header(
        _authorization_header(request)
    )
    FoundationPermissionService().require_permission(user, "knowledge", action)
    return user


def _require_internal_pilot_user(request):
    """Allow internal RAG only for explicitly enabled department pilot users."""
    user = _require_knowledge_user(request, "read")
    if not PilotProgramService().is_running():
        KnowledgeAuditEvent.objects.create(
            event="denied", decision="denied", actor_id=user.id,
        )
        raise PermissionDenied("The internal AI pilot is not running.")
    if not KnowledgeUserScope.objects.filter(
        user=user, pilot_enabled=True, approval_status="APPROVED",
        approved_at__isnull=False, training_acknowledged_at__isnull=False,
    ).filter(Q(expires_at__isnull=True) | Q(expires_at__gte=timezone.now())).exists():
        KnowledgeAuditEvent.objects.create(
            event="denied", decision="denied", actor_id=user.id,
        )
        raise PermissionDenied("Internal AI pilot access is not enabled for this user.")
    return user




def _require_management_reviewer(request):
    """Require an approved Management pilot reviewer with write permission."""
    user = _require_internal_pilot_user(request)
    FoundationPermissionService().require_permission(user, "knowledge", "write")
    if user.knowledge_scope.department != "MANAGEMENT":
        raise PermissionDenied("Human evaluation requires a Management pilot reviewer.")
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
@parser_classes([JSONParser, MultiPartParser, FormParser])
def knowledge_documents(request):
    """List or create internal knowledge documents."""
    action = "write" if request.method == "POST" else "read"
    try:
        user = _require_knowledge_user(request, action)
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    service = KnowledgeService()
    if request.method == "GET":
        return ok(
            [
                document_to_dict(document)
                for document in service.list_documents(user=user)
            ]
        )

    serializer = KnowledgeDocumentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    uploaded_file = request.FILES.get("file")
    if uploaded_file:
        try:
            processed = DocumentProcessor().process_uploaded_file(uploaded_file)
        except (ValidationError, ValueError) as exc:
            message = "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc)
            return Response(
                {
                    "success": False,
                    "error": {"code": "unsafe_upload", "message": message},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        content = processed["text"]
        source_type = processed["source_type"]
        storage_path = default_storage.save(
            f"knowledge/uploads/{processed['source_path']}",
            uploaded_file,
        )
        source_path = storage_path
    else:
        content = data.get("content", "")
        source_type = data.get("source_type") or "text"
        source_path = ""

    cleanup_context = (
        stored_file_cleanup(source_path) if uploaded_file else stored_file_cleanup("")
    )
    with cleanup_context:
        document = service.create_document(
            title=data["title"],
            description=data.get("description", ""),
            category_name=data.get("category", ""),
            content=content,
            source_type=source_type,
            source_path=source_path,
            permission_level=data.get("permission_level", "internal"),
            department=data.get("department", ""),
            owner_email=data.get("owner_email", ""),
            effective_date=data.get("effective_date"),
            created_by_email=user.email,
            metadata=data.get("metadata") or {},
        )
    return created(document_to_dict(document))


@api_view(["POST"])
@permission_classes([AllowAny])
def knowledge_document_transition(request, document_id, transition):
    """Explicit staff review/approval/archive, never implicit at upload."""
    try:
        user = _require_knowledge_user(request, "write")
        service = KnowledgeGovernanceService()
        if transition == "review":
            document = service.submit_review(document_id, actor=user)
        elif transition == "owner-review":
            document = PilotGovernanceService().record_owner_review(document_id, actor=user)
        elif transition == "approve":
            release = serializers.BooleanField(required=False, default=False)
            value = release.run_validation(request.data.get("release_public", False))
            document = service.approve(document_id, actor=user, release_public=value)
        elif transition == "archive":
            document = service.archive(document_id, actor=user)
        elif transition == "pilot-approve":
            document = PilotGovernanceService().approve_document(document_id, actor=user)
        elif transition == "quality-review":
            review = KnowledgeQualityReviewSerializer(data=request.data)
            review.is_valid(raise_exception=True)
            document = PilotGovernanceService().record_quality_review(
                document_id, actor=user, **review.validated_data,
            )
        else:
            raise Http404("Unknown transition.")
    except KnowledgeDocument.DoesNotExist as exc:
        raise Http404("Knowledge document not found.") from exc
    except PermissionDenied as exc:
        KnowledgeAuditEvent.objects.create(event="denied", decision="denied", actor_id=getattr(locals().get("user"), "id", None), document_id_snapshot=document_id)
        return _permission_error_response(exc)
    except ValidationError as exc:
        return Response({"success": False, "error": {"code": "invalid_transition", "message": "; ".join(exc.messages)}}, status=status.HTTP_400_BAD_REQUEST)
    return ok(document_to_dict(document))


@api_view(["POST"])
@permission_classes([AllowAny])
def knowledge_pilot_user_transition(request, scope_id, transition):
    """Explicitly approve or revoke one bounded pilot-user scope."""
    try:
        user = _require_knowledge_user(request, "write")
        service = PilotGovernanceService()
        if transition == "approve":
            expires = serializers.DateTimeField(required=False, allow_null=True)
            expires_at = expires.run_validation(request.data.get("expires_at"))
            scope = service.approve_user_scope(scope_id, actor=user, expires_at=expires_at)
        elif transition == "revoke":
            scope = service.revoke_user_scope(scope_id, actor=user)
        else:
            raise Http404("Unknown transition.")
    except KnowledgeUserScope.DoesNotExist as exc:
        raise Http404("Pilot user scope not found.") from exc
    except PermissionDenied as exc:
        return _permission_error_response(exc)
    except ValidationError as exc:
        return Response(
            {"success": False, "error": {"code": "invalid_transition", "message": "; ".join(exc.messages)}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return ok({
        "scope_id": scope.id,
        "user_id": scope.user_id,
        "department": scope.department,
        "pilot_enabled": scope.pilot_enabled,
        "approval_status": scope.approval_status,
        "approved_at": scope.approved_at.isoformat() if scope.approved_at else None,
        "expires_at": scope.expires_at.isoformat() if scope.expires_at else None,
        "training_acknowledged_at": scope.training_acknowledged_at.isoformat() if scope.training_acknowledged_at else None,
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def knowledge_pilot_training_acknowledgement(request):
    """Record the approved pilot user's acknowledgement of the usage guide."""
    try:
        user = _require_knowledge_user(request, "read")
        scope = KnowledgeUserScope.objects.get(user=user)
        scope = PilotGovernanceService().acknowledge_training(scope.id, actor=user)
    except KnowledgeUserScope.DoesNotExist as exc:
        raise Http404("Pilot user scope not found.") from exc
    except PermissionDenied as exc:
        return _permission_error_response(exc)
    return ok({
        "scope_id": scope.id,
        "training_acknowledged_at": scope.training_acknowledged_at.isoformat(),
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def knowledge_document_download(request, document_id):
    """Stream an authorized private upload without exposing its filesystem path."""
    try:
        user = _require_knowledge_user(request)
    except PermissionDenied as exc:
        return _permission_error_response(exc)
    try:
        document = KnowledgeService().list_documents(user=user).get(id=document_id)
    except KnowledgeDocument.DoesNotExist as exc:
        raise Http404("Knowledge document not found.") from exc
    source_path = str(document.source_path or "").replace("\\", "/")
    path = PurePosixPath(source_path)
    if (
        path.is_absolute()
        or ".." in path.parts
        or path.parts[:2] != ("knowledge", "uploads")
    ):
        raise Http404("Private upload is unavailable.")
    if not default_storage.exists(source_path):
        raise Http404("Private upload is unavailable.")
    return FileResponse(
        default_storage.open(source_path, "rb"),
        as_attachment=True,
        filename=path.name,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def knowledge_search(request):
    """Search the local knowledge base and return relevant chunks."""
    try:
        user = _require_internal_pilot_user(request)
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
            ip_address=request.META.get("REMOTE_ADDR", ""),
            module="knowledge",
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
        user = _require_internal_pilot_user(request)
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
            ip_address=request.META.get("REMOTE_ADDR", ""),
            module="knowledge",
        )
    except AIGovernanceError as exc:
        return _governance_error_response(exc)

    result = KnowledgeAssistantService().answer(
        question,
        user=user,
        limit=serializer.validated_data["limit"],
    )
    return ok(result)








@api_view(["POST"])
@permission_classes([AllowAny])
def knowledge_feedback(request):
    """Record one structured feedback category for the caller's interaction."""
    try:
        user = _require_internal_pilot_user(request)
    except PermissionDenied as exc:
        return _permission_error_response(exc)
    serializer = KnowledgeFeedbackSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        interaction = KnowledgeAssistantLog.objects.get(
            pk=serializer.validated_data["interaction_id"], user_email=user.email,
        )
    except KnowledgeAssistantLog.DoesNotExist as exc:
        raise Http404("Interaction not found.") from exc
    feedback, _created = KnowledgeAssistantFeedback.objects.update_or_create(
        interaction=interaction, submitted_by=user,
        defaults={"category": serializer.validated_data["category"]},
    )
    KnowledgeAuditEvent.objects.create(
        event="feedback", actor_id=user.id, decision="allowed", source_ids=[],
    )
    return ok({"interaction_id": interaction.id, "category": feedback.category})


@api_view(["POST"])
@permission_classes([AllowAny])
def knowledge_human_evaluation(request):
    """Record a Management review without copying question or answer content."""
    try:
        reviewer = _require_management_reviewer(request)
    except PermissionDenied as exc:
        return _permission_error_response(exc)
    serializer = KnowledgeHumanEvaluationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        interaction = KnowledgeAssistantLog.objects.get(
            pk=serializer.validated_data["interaction_id"]
        )
    except KnowledgeAssistantLog.DoesNotExist as exc:
        raise Http404("Interaction not found.") from exc
    evaluation, _created = KnowledgeHumanEvaluation.objects.update_or_create(
        interaction=interaction,
        defaults={
            "reviewer": reviewer,
            "question_category": serializer.validated_data["question_category"],
            "rating": serializer.validated_data["rating"],
            "citation_valid": serializer.validated_data["citation_valid"],
            "permission_correct": serializer.validated_data["permission_correct"],
            "missing_information": serializer.validated_data["missing_information"],
            "hallucination": serializer.validated_data["hallucination"],
        },
    )
    KnowledgeAuditEvent.objects.create(
        event="human_evaluation", actor_id=reviewer.id,
        decision="allowed", source_ids=[],
    )
    return ok({
        "interaction_id": interaction.id,
        "question_category": evaluation.question_category,
        "rating": evaluation.rating,
        "citation_valid": evaluation.citation_valid,
        "permission_correct": evaluation.permission_correct,
        "missing_information": evaluation.missing_information,
        "hallucination": evaluation.hallucination,
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def knowledge_gap_review(request):
    """Classify one knowledge failure without copying sensitive content."""
    try:
        reviewer = _require_management_reviewer(request)
    except PermissionDenied as exc:
        return _permission_error_response(exc)
    serializer = KnowledgeGapReviewSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        interaction = KnowledgeAssistantLog.objects.get(
            pk=serializer.validated_data["interaction_id"]
        )
    except KnowledgeAssistantLog.DoesNotExist as exc:
        raise Http404("Interaction not found.") from exc
    gap, _created = KnowledgeGapReview.objects.update_or_create(
        interaction=interaction,
        defaults={
            "reviewer": reviewer,
            "category": serializer.validated_data["category"],
            "resolved": serializer.validated_data["resolved"],
        },
    )
    KnowledgeAuditEvent.objects.create(
        event="gap_review", actor_id=reviewer.id,
        decision="allowed", source_ids=[],
    )
    return ok({
        "interaction_id": interaction.id,
        "category": gap.category,
        "resolved": gap.resolved,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def knowledge_pilot_monitoring(request):
    """Return content-free pilot metrics to knowledge operators."""
    try:
        _require_knowledge_user(request, "write")
    except PermissionDenied as exc:
        return _permission_error_response(exc)
    readiness = PilotProgramService().readiness()
    return ok({
        **PilotMonitoringService().snapshot(),
        "active_users": sum(readiness["department_user_counts"].values()),
        "launch_readiness": readiness,
        "program_running": PilotProgramService().is_running(),
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def knowledge_pilot_program_transition(request, transition):
    """Launch or immediately suspend the bounded internal pilot."""
    try:
        user = _require_knowledge_user(request, "write")
        service = PilotProgramService()
        if transition == "launch":
            serializer = KnowledgePilotLaunchSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            program = service.launch(actor=user, **serializer.validated_data)
        elif transition == "suspend":
            program = service.suspend(actor=user)
        else:
            raise Http404("Unknown transition.")
    except PermissionDenied as exc:
        return _permission_error_response(exc)
    except ValidationError as exc:
        return Response(
            {"success": False, "error": {"code": "pilot_not_ready", "message": "; ".join(exc.messages)}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return ok({
        "name": program.name, "status": program.status,
        "planned_start": program.planned_start.isoformat() if program.planned_start else None,
        "planned_end": program.planned_end.isoformat() if program.planned_end else None,
    })




@api_view(["GET"])
@permission_classes([AllowAny])
def knowledge_health(request):
    """Return permission-protected RAG/model/vector health for operators."""
    try:
        _require_knowledge_user(request)
    except PermissionDenied as exc:
        return _permission_error_response(exc)
    return ok(KnowledgeRuntimeHealthService().check())

class SyntheticRagDemoSerializer(serializers.Serializer):
    """Validate one bounded internal synthetic-demo question."""

    question = serializers.CharField(
        max_length=1200, allow_blank=False, trim_whitespace=True
    )

def _require_synthetic_rag_demo_user(request):
    """Allow knowledge-enabled internal roles, while denying read-only viewers."""

    user = _require_knowledge_user(request, "read")
    if user.role.name.casefold() not in {"admin", "manager", "sales", "editor"}:
        KnowledgeAuditEvent.objects.create(
            event="denied", decision="denied", actor_id=user.id,
        )
        raise PermissionDenied("The synthetic RAG demo is restricted to internal staff roles.")
    return user

@api_view(["POST"])
@permission_classes([AllowAny])
def synthetic_rag_demo_query(request):
    """Query only the controlled Phase 3 synthetic Product corpus."""

    try:
        user = _require_synthetic_rag_demo_user(request)
    except PermissionDenied as exc:
        return _permission_error_response(exc)
    serializer = SyntheticRagDemoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    question = serializer.validated_data["question"]
    try:
        AIGovernanceService().enforce(
            user=user,
            endpoint="internal/rag-demo/query",
            action="chat",
            text=question,
            metadata={"dataset_id": "rag_synthetic_demo_v1", "limit": 3},
            ip_address=request.META.get("REMOTE_ADDR", ""),
            module="knowledge",
        )
    except AIGovernanceError as exc:
        return _governance_error_response(exc)
    return ok(SyntheticRagWebDemoService().query(question, user=user, limit=3))

class SyntheticRagChatSerializer(serializers.Serializer):
    """Validate a bounded message for the internal conversational demo."""

    message = serializers.CharField(
        max_length=1200, allow_blank=False, trim_whitespace=True
    )

@api_view(["POST"])
@permission_classes([AllowAny])
def synthetic_rag_chat(request):
    """Expose the same isolated synthetic RAG pipeline as a chat-shaped API."""

    try:
        user = _require_synthetic_rag_demo_user(request)
    except PermissionDenied as exc:
        return _permission_error_response(exc)
    serializer = SyntheticRagChatSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    message = serializer.validated_data["message"]
    try:
        AIGovernanceService().enforce(
            user=user,
            endpoint="internal/rag-chat",
            action="chat",
            text=message,
            metadata={"dataset_id": "rag_synthetic_demo_v1", "limit": 3},
            ip_address=request.META.get("REMOTE_ADDR", ""),
            module="knowledge",
        )
    except AIGovernanceError as exc:
        return _governance_error_response(exc)
    result = SyntheticRagWebDemoService().query(message, user=user, limit=3)
    return ok({"question": message, **result})

