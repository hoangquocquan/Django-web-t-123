"""Canonical, advisory-only AI endpoints for authenticated business users."""

from rest_framework import serializers

from apps.ai.services.governance_service import AIGovernanceError, AIGovernanceService
from apps.ai_agent.services.sales_assistant import SalesAssistantService
from apps.api.canonical_contract import CanonicalApiError, CanonicalAPIView, success
from apps.api.canonical_permissions import CanonicalAIUsePermission
from apps.knowledge.services.assistant_service import KnowledgeAssistantService


class CanonicalSalesAssistantSerializer(serializers.Serializer):
    """Validate the bounded Sales AI action contract."""

    action = serializers.ChoiceField(
        choices=[
            "lead_analysis",
            "customer_summary",
            "email_draft",
            "weekly_recommendation",
        ]
    )
    payload = serializers.DictField(required=False, default=dict)


class CanonicalKnowledgeAssistantSerializer(serializers.Serializer):
    """Validate one source-grounded internal knowledge question."""

    question = serializers.CharField(
        max_length=1200,
        allow_blank=False,
        trim_whitespace=True,
    )
    limit = serializers.IntegerField(min_value=1, max_value=10, default=5)


class CanonicalAIView(CanonicalAPIView):
    """Base POST-only AI view with exact canonical permission enforcement."""

    http_method_names = ["post", "options"]
    permission_classes = [CanonicalAIUsePermission]
    permission_code = ""

    def get_permission_code(self):
        return self.permission_code

    def enforce_governance(self, request, *, endpoint, action, text, metadata=None):
        try:
            return AIGovernanceService().enforce(
                user=request.user,
                endpoint=endpoint,
                action=action,
                text=text,
                metadata=metadata or {},
                ip_address=request.META.get("REMOTE_ADDR", ""),
                module=self.permission_code.split(":", 1)[0],
                request_source="canonical-api",
            )
        except AIGovernanceError as exc:
            raise CanonicalApiError(
                exc.code,
                exc.message,
                status_code=exc.status_code,
            ) from exc


class CanonicalSalesAssistantView(CanonicalAIView):
    """Return grounded Sales suggestions without executing business writes."""

    permission_code = "ai_sales:read"
    resource_name = "AI Sales request"

    def post(self, request):
        serializer = CanonicalSalesAssistantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        payload = serializer.validated_data["payload"]
        self.enforce_governance(
            request,
            endpoint="canonical/ai/sales-assistant",
            action=action,
            text=" ".join(str(value) for value in payload.values()),
            metadata={"action": action},
        )
        result = SalesAssistantService().handle(
            action=action,
            payload=payload,
            user=request.user,
        )
        return success(result)


class CanonicalKnowledgeAssistantView(CanonicalAIView):
    """Answer internal questions from documents visible to the caller."""

    permission_code = "knowledge:read"
    resource_name = "Knowledge request"

    def post(self, request):
        serializer = CanonicalKnowledgeAssistantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]
        limit = serializer.validated_data["limit"]
        self.enforce_governance(
            request,
            endpoint="canonical/ai/knowledge-assistant",
            action="chat",
            text=question,
            metadata={"limit": limit},
        )
        result = KnowledgeAssistantService().answer(
            question,
            user=request.user,
            limit=limit,
        )
        return success(result)
