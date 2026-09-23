"""RAG assistant service that answers with source references."""

from __future__ import annotations

from django.conf import settings
from django.db import transaction

from apps.ai.services.ollama_client import OllamaClient
from apps.knowledge.models import KnowledgeAssistantLog, KnowledgeDocument
from apps.knowledge.services.access_policy import KnowledgeAccessPolicy
from apps.knowledge.services.business_connector import BusinessKnowledgeConnector
from apps.knowledge.services.rag_pipeline import AIRequestLogService, RagGenerationPipeline, RagPromptTemplate
from apps.knowledge.services.search_service import KnowledgeSearchService


class KnowledgeAssistantService:
    """Answer internal MEC questions using local knowledge and Ollama."""

    def __init__(self, search_service=None, ollama_client=None, business_connector=None):
        """Allow tests to inject local doubles."""
        self.search_service = search_service or KnowledgeSearchService()
        self.ollama_client = ollama_client or OllamaClient()
        self.business_connector = business_connector or BusinessKnowledgeConnector()

    @transaction.atomic
    def answer(self, question, user=None, limit=5):
        """Retrieve context, call Ollama when safe, and audit the answer."""
        retrieval = self.search_service.search(question, limit=limit, user=user)
        sources = retrieval["sources"]
        confidence = retrieval["confidence"]
        warning = ""
        minimum_generation_confidence = float(
            getattr(settings, "KNOWLEDGE_ASSISTANT_MIN_CONFIDENCE", 0.5)
        )
        if sources and confidence < minimum_generation_confidence:
            retrieval = {**retrieval, "results": [], "sources": []}
            sources = []
            warning = (
                "Retrieved source relevance is below the assistant confidence "
                "threshold; the assistant did not ask the model to answer."
            )

        if not sources:
            answer = "Không tìm thấy tài liệu phù hợp để trả lời chắc chắn."
            warning = warning or "No relevant source context found. The assistant did not ask the model to invent an answer."
            model = getattr(self.ollama_client, "model", "local-model")
            response_time_ms = 0
            generation_status = "blocked_no_context"
            source_relevance_score = 0
            hallucination_warning = warning
            AIRequestLogService().log(
                user=user,
                question=question,
                retrieval=retrieval,
                model=model,
                response_time_ms=response_time_ms,
                confidence=confidence,
                warning=warning,
                status=generation_status,
            )
        else:
            result = RagGenerationPipeline(ollama_client=self.ollama_client).generate(
                question,
                retrieval,
                user=user,
                fallback_builder=self._fallback_answer,
            )
            answer = result["answer"]
            warning = result["warning"]
            confidence = result["confidence"]
            model = result["model"]
            response_time_ms = result["response_time_ms"]
            generation_status = result["generation_status"]
            source_relevance_score = result["source_relevance_score"]
            hallucination_warning = result["hallucination_warning"]

        if confidence < 0.35:
            warning = warning or "Low confidence. Please verify the cited sources."

        if sources and not KnowledgeAccessPolicy().sources_still_readable(sources, user):
            answer = "Nguồn đã thay đổi hoặc quyền truy cập đã bị thu hồi. Vui lòng thử lại."
            sources = []
            confidence = 0
            warning = "Source authorization changed during answer generation."
            generation_status = "blocked_revoked"
            source_relevance_score = 0
            hallucination_warning = warning

        interaction = KnowledgeAssistantLog.objects.create(
            question="",
            answer="",
            sources=[{"id": source.get("id"), "version": source.get("version")} for source in sources],
            confidence=confidence,
            warning=warning,
            user_email=getattr(user, "email", "") or "",
        )
        return {
            "interaction_id": interaction.id,
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "warning": warning,
            "model": model,
            "provider": "ollama-local" if generation_status == "generated" else "source-fallback",
            "response_time_ms": response_time_ms,
            "generation_status": generation_status,
            "source_relevance_score": source_relevance_score,
            "hallucination_warning": hallucination_warning,
        }

    def _build_prompt(self, question, retrieval):
        """Build a source-grounded prompt for the local model."""
        context = {
            "knowledge_context": "\n".join(
                f"[{index}] {result['document']['title']}: {result['chunk']['content']}"
                for index, result in enumerate(retrieval["results"], start=1)
            ),
            "business_context": self.business_connector.build_context(question),
        }
        return RagPromptTemplate().build(question, context)

    def _fallback_answer(self, question, retrieval):
        """Return a deterministic answer when Ollama is offline."""
        if not retrieval["results"]:
            return "Không có ngữ cảnh phù hợp để trả lời."
        titles = ", ".join(source["title"] for source in retrieval["sources"])
        return f"Có tài liệu liên quan: {titles}. Vui lòng kiểm tra các nguồn được trích dẫn."


