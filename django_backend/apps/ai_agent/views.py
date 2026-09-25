"""API views for the local AI agent system."""

from __future__ import annotations

import time
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.ai.models import AIGovernanceEvent
from apps.ai_agent.services.ai_sales_metrics import AISalesMetricsService
from apps.ai_agent.services.agent_controller import AgentControlError, AgentController
from apps.ai_agent.services.sales_assistant import SalesAssistantService
from apps.api.views.helpers import ok
from apps.ai.services.governance_service import AIGovernanceError, AIGovernanceService
from apps.foundation.services import FoundationAuthService, FoundationPermissionService
from apps.sales.services.rfq_access_service import RfqAccessService


class AgentRunSerializer(serializers.Serializer):
    """Validate an agent execution request."""

    request = serializers.CharField(max_length=2000, allow_blank=False, trim_whitespace=True)


class SalesAssistantSerializer(serializers.Serializer):
    """Validate a safe AI Sales Assistant request."""

    action = serializers.ChoiceField(
        choices=["lead_analysis", "customer_summary", "email_draft", "weekly_recommendation"]
    )
    payload = serializers.DictField(required=False, default=dict)


class AISalesAnalyzeSerializer(serializers.Serializer):
    """Validate a canonical RFQ reference or bounded synthetic sales case."""

    rfq_id = serializers.IntegerField(required=False, min_value=1)
    customer_name = serializers.CharField(required=False, allow_blank=True, max_length=220)
    request = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    material = serializers.CharField(required=False, allow_blank=True, max_length=160)
    quantity = serializers.DecimalField(
        required=False, max_digits=16, decimal_places=4, min_value=Decimal("0.0001")
    )
    process = serializers.CharField(required=False, allow_blank=True, max_length=240)
    tolerance = serializers.CharField(required=False, allow_blank=True, max_length=120)
    surface_treatment = serializers.CharField(required=False, allow_blank=True, max_length=160)
    drawing_available = serializers.BooleanField(required=False, allow_null=True)
    deadline = serializers.DateField(required=False)

    def validate(self, attrs):
        if attrs.get("rfq_id") and any(key != "rfq_id" for key in attrs):
            raise serializers.ValidationError("rfq_id cannot be combined with synthetic request fields.")
        if not attrs.get("rfq_id") and not str(attrs.get("request", "")).strip():
            raise serializers.ValidationError("request is required when rfq_id is not provided.")
        return attrs


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


def _require_internal_ai_sales_user(request):
    """Require both AI Sales and canonical sales visibility grants."""
    user = FoundationAuthService().user_from_authorization_header(_authorization_header(request))
    if str(getattr(getattr(user, "role", None), "name", "")).casefold() == "viewer":
        raise PermissionDenied("Viewer role is not authorized for private AI Sales data.")
    permissions = FoundationPermissionService()
    permissions.require_permission(user, "ai_sales", "read")
    permissions.require_permission(user, "sales", "read")
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
            ip_address=request.META.get("REMOTE_ADDR", ""),
            module="ai_agent",
            tool="agent-controller",
        )
    except AIGovernanceError as exc:
        return _governance_error_response(exc)

    try:
        result = AgentController().run(request_text, user=user)
    except AgentControlError as exc:
        return Response(
            {"success": False, "error": {"code": exc.code, "message": str(exc)}},
            status=status.HTTP_400_BAD_REQUEST,
        )
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
            ip_address=request.META.get("REMOTE_ADDR", ""),
            module="ai_sales",
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


@api_view(["POST"])
@permission_classes([AllowAny])
def internal_ai_sales_analyze(request):
    """Analyze one RFQ or synthetic opportunity; never execute a sales action."""
    try:
        user = _require_internal_ai_sales_user(request)
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    serializer = AISalesAnalyzeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data
    input_reference = f"rfq:{payload['rfq_id']}" if payload.get("rfq_id") else "synthetic:ad-hoc"
    governance = AIGovernanceService()
    try:
        decision = governance.enforce(
            user=user,
            endpoint="internal/ai-sales/analyze",
            action="sales_analysis",
            text=" ".join(
                str(payload.get(field, ""))
                for field in ("request", "material", "process", "surface_treatment", "tolerance")
            ),
            metadata={"input_reference": input_reference},
            ip_address=request.META.get("REMOTE_ADDR", ""),
            module="ai_sales",
            tool="governed-rag",
        )
    except AIGovernanceError as exc:
        return _governance_error_response(exc)

    started = time.perf_counter()
    try:
        result = SalesAssistantService().analyze(payload, user=user)
    except ValidationError as exc:
        return _validation_error_response(exc)
    except ObjectDoesNotExist:
        return Response(
            {"success": False, "error": {"code": "not_found", "message": "Requested RFQ was not found."}},
            status=status.HTTP_404_NOT_FOUND,
        )

    duration_seconds = time.perf_counter() - started
    bounded_metrics = AISalesMetricsService().record(
        result, duration_seconds=duration_seconds
    )
    result.pop("_telemetry", None)
    source_ids = [source.get("id") for source in result.get("sources", []) if source.get("id") is not None]
    AIGovernanceEvent.objects.filter(correlation_id=decision.correlation_id).update(
        metadata={
            "input_reference": result["input_reference"],
            "result_status": result["status"],
            "priority": result["priority"],
            "source_ids": source_ids,
            "latency_ms": int(duration_seconds * 1000),
            "retrieval": bounded_metrics["retrieval"],
            "provider": bounded_metrics["provider"],
            "deterministic_fallback": bounded_metrics["deterministic_fallback"],
        }
    )
    result["request_id"] = decision.correlation_id
    return ok(result)


@api_view(["GET"])
@permission_classes([AllowAny])
def internal_ai_sales_rfqs(request):
    """Return only scoped, minimized RFQ metadata for the internal selector."""
    try:
        user = _require_internal_ai_sales_user(request)
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    queryset = RfqAccessService().visible_queryset(user).order_by("-created_at", "-id")
    rfqs = list(queryset[:100])
    return ok(
        {
            "count": len(rfqs),
            "results": [
                {
                    "id": rfq.pk,
                    "rfq_number": rfq.rfq_number,
                    "status": rfq.status,
                    "project_name": rfq.project_name,
                    "customer_display": (
                        rfq.customer.company_name or rfq.customer.contact_name
                    ),
                    "quote_due_at": str(rfq.quote_due_at),
                    "required_delivery_date": str(rfq.required_delivery_date),
                }
                for rfq in rfqs
            ],
        }
    )
