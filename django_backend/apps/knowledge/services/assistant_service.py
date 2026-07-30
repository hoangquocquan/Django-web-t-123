"""RAG assistant service that answers with source references."""

from __future__ import annotations

from django.db import transaction

from apps.ai.services.ollama_client import OllamaClient, OllamaClientError
from apps.knowledge.models import KnowledgeAssistantLog, KnowledgeDocument
from apps.knowledge.services.business_connector import BusinessKnowledgeConnector
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
        else:
            prompt = self._build_prompt(question, retrieval)
            try:
                answer = self.ollama_client.generate_response(prompt).answer
            except OllamaClientError:
                answer = self._fallback_answer(question, retrieval)
                warning = "Ollama is unavailable; returned source-based fallback answer."

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
        }

    def _build_prompt(self, question, retrieval):
        """Build a source-grounded prompt for the local model."""
        context_lines = []
        for index, result in enumerate(retrieval["results"], start=1):
            source = result["document"]["title"]
            context_lines.append(f"[{index}] {source}: {result['chunk']['content']}")
        business_context = self.business_connector.build_context(question)
        return (
            "You are MEC Precision internal knowledge assistant. "
            "Answer only from the provided context. Cite source titles. "
            "If context is insufficient, say so.\n\n"
            f"Question: {question}\n\n"
            f"Knowledge context:\n{chr(10).join(context_lines)}\n\n"
            f"Read-only business context:\n{business_context}"
        )

    def _fallback_answer(self, question, retrieval):
        """Return a deterministic answer when Ollama is offline."""
        if not retrieval["results"]:
            return "Không có ngữ cảnh phù hợp để trả lời."
        titles = ", ".join(source["title"] for source in retrieval["sources"])
        return f"Có tài liệu liên quan: {titles}. Vui lòng kiểm tra các nguồn được trích dẫn."
