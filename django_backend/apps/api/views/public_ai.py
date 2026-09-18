"""Anonymous AI endpoint restricted to explicitly public knowledge."""

from django.conf import settings
from rest_framework import serializers
from rest_framework.permissions import AllowAny

from apps.ai.services.governance_service import AIGovernanceError, AIGovernanceService
from apps.api.canonical_contract import CanonicalApiError, CanonicalAPIView, success
from apps.knowledge.services.assistant_service import PublicKnowledgeAssistantService


class PublicAssistantSerializer(serializers.Serializer):
    """Validate a short public product or capability question."""

    question = serializers.CharField(
        max_length=800,
        allow_blank=False,
        trim_whitespace=True,
    )


class PublicAssistantView(CanonicalAPIView):
    """Answer from public documents without authenticating or exposing internals."""

    authentication_classes = []
    permission_classes = [AllowAny]
    http_method_names = ["post", "options"]
    resource_name = "Public AI request"

    def post(self, request):
        serializer = PublicAssistantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]
        try:
            AIGovernanceService().enforce(
                user=None,
                endpoint="public/ai/assistant",
                action="chat",
                text=question,
                limit=int(getattr(settings, "AI_PUBLIC_RATE_LIMIT_PER_IP", 10)),
                ip_address=request.META.get("REMOTE_ADDR", ""),
                module="public_ai",
                request_source="public-website",
            )
        except AIGovernanceError as exc:
            raise CanonicalApiError(
                exc.code,
                exc.message,
                status_code=exc.status_code,
            ) from exc

        return success(PublicKnowledgeAssistantService().answer(question, limit=3))
