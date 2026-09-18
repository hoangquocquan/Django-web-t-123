"""RAG assistant service that answers with source references."""

from __future__ import annotations

from django.db import transaction

from apps.ai.services.ollama_client import OllamaClient
from apps.knowledge.models import KnowledgeAssistantLog, KnowledgeDocument
from apps.knowledge.services.business_connector import BusinessKnowledgeConnector
from apps.knowledge.services.rag_pipeline import (
    AIRequestLogService,
    RagContextBuilder,
    RagGenerationPipeline,
    RagPromptTemplate,
)
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

        if KnowledgeDocument.objects.exists() and not sources:
            answer = "Không tìm thấy tài liệu phù hợp để trả lời chắc chắn."
            warning = "No relevant source context found. The assistant did not ask the model to invent an answer."
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
            result = RagGenerationPipeline(
                ollama_client=self.ollama_client,
                context_builder=RagContextBuilder(
                    business_connector=self.business_connector
                ),
            ).generate(
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

        KnowledgeAssistantLog.objects.create(
            question=question,
            answer=answer,
            sources=sources,
            confidence=confidence,
            warning=warning,
            user_email=getattr(user, "email", "") or "",
        )
        return {
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


class PublicKnowledgeAssistantService:
    """Public RAG facade that cannot expose private documents or metadata."""

    def __init__(self, assistant=None):
        if assistant is None:
            from apps.knowledge.services.business_connector import (
                PublicBusinessKnowledgeConnector,
            )

            assistant = KnowledgeAssistantService(
                business_connector=PublicBusinessKnowledgeConnector()
            )
        self.assistant = assistant

    def answer(self, question, limit=3):
        """Answer from public documents and return a minimal source contract."""
        result = self.assistant.answer(question, user=None, limit=limit)
        result["sources"] = [
            {
                "id": source.get("id"),
                "title": source.get("title", ""),
                "description": source.get("description", ""),
                "category": source.get("category"),
                "relevance_score": source.get("relevance_score", 0),
            }
            for source in result.get("sources", [])
        ]
        result["scope"] = "public_knowledge_only"
        result["contact_recommended"] = not bool(result["sources"])
        return result
