"""Source-grounded RAG pipeline for local Ollama inference."""

from __future__ import annotations

import time
import hashlib
from inspect import signature

from apps.ai.models import AIRequestLog
from apps.ai.services.model_config import AIModelConfigService
from apps.ai.services.ollama_client import OllamaClient, OllamaClientError
from apps.knowledge.services.business_connector import BusinessKnowledgeConnector


class RagContextBuilder:
    """Build ranked context lines from semantic search results."""

    def __init__(self, business_connector=None):
        """Allow tests to inject a simple business-context provider."""
        self.business_connector = business_connector or BusinessKnowledgeConnector()

    def build(self, question, retrieval, user=None):
        """Return compact model context while keeping source metadata."""
        ranked_results = sorted(
            retrieval.get("results", []),
            key=lambda result: result.get("score", 0),
            reverse=True,
        )
        context_lines = []
        for index, result in enumerate(ranked_results, start=1):
            source_title = result["document"]["title"]
            score = round(result.get("score", 0), 4)
            content = result["chunk"]["content"]
            context_lines.append(f"[{index}] {source_title} | relevance={score}: {content}")
        return {
            "knowledge_context": "\n".join(context_lines),
            "business_context": self.business_connector.build_context(question, user=user),
            "ranked_results": ranked_results,
        }


class RagPromptTemplate:
    """Create a safe prompt that tells the model to answer only from sources."""

    def build(self, question, context):
        """Return the final prompt sent to local Ollama."""
        return (
            "You are MEC Precision VIETNAM's source-grounded AI assistant.\n"
            "Rules:\n"
            "- Answer only from the provided knowledge context and read-only business context.\n"
            "- Cite source titles when making a factual claim.\n"
            "- If the context is insufficient, say that more information is needed.\n"
            "- Do not create orders, quotes, emails, or business actions automatically.\n\n"
            f"Question:\n{question}\n\n"
            f"Knowledge context:\n{context['knowledge_context']}\n\n"
            f"Read-only business context:\n{context['business_context']}"
        )


class RagAnswerEvaluator:
    """Evaluate answer quality using explainable, local-only heuristics."""

    def evaluate(self, answer, retrieval):
        """Return confidence and hallucination warning from retrieved sources."""
        sources = retrieval.get("sources", [])
        confidence = float(retrieval.get("confidence", 0) or 0)
        best_relevance = 0.0
        for source in sources:
            best_relevance = max(best_relevance, float(source.get("relevance_score", 0) or 0))

        source_titles = [source.get("title", "") for source in sources]
        cites_source = any(title and title in answer for title in source_titles)
        hallucination_warning = ""
        if sources and not cites_source:
            hallucination_warning = "Answer does not explicitly cite a retrieved source title."
        if confidence < 0.35:
            hallucination_warning = hallucination_warning or "Low confidence. Please verify the cited sources."

        adjusted_confidence = confidence
        if sources and not cites_source:
            adjusted_confidence = min(confidence, 0.6)

        return {
            "confidence": round(adjusted_confidence, 4),
            "source_relevance_score": round(best_relevance, 4),
            "hallucination_warning": hallucination_warning,
            "source_citation_found": cites_source,
        }


class AIRequestLogService:
    """Persist AI request metadata without storing unnecessary secrets."""

    def log(self, *, user, question, retrieval, model, response_time_ms, confidence, warning, status):
        """Create one monitoring row for audit and troubleshooting."""
        normalized_question = " ".join(str(question).split())
        return AIRequestLog.objects.create(
            user_email=getattr(user, "email", "") or "",
            question_hash=hashlib.sha256(normalized_question.encode("utf-8")).hexdigest(),
            question_preview="",
            retrieved_documents=[
                {
                    "id": source.get("id"),
                    "version": source.get("version"),
                    "relevance_score": source.get("relevance_score", 0),
                }
                for source in retrieval.get("sources", [])
            ],
            model_name=model,
            response_time_ms=response_time_ms,
            confidence=confidence,
            warning=warning,
            status=status,
        )


class RagGenerationPipeline:
    """Run retrieval context through local Ollama and return cited output."""

    def __init__(
        self,
        ollama_client=None,
        config_service=None,
        context_builder=None,
        prompt_template=None,
        evaluator=None,
        logger=None,
        answer_transformer=None,
    ):
        """Allow tests to inject fake dependencies without calling real Ollama."""
        self.config_service = config_service or AIModelConfigService()
        self.ollama_client = ollama_client
        self.context_builder = context_builder or RagContextBuilder()
        self.prompt_template = prompt_template or RagPromptTemplate()
        self.evaluator = evaluator or RagAnswerEvaluator()
        self.logger = logger or AIRequestLogService()
        self.answer_transformer = answer_transformer

    def generate(self, question, retrieval, user=None, fallback_builder=None):
        """Generate a source-grounded answer and log the AI request."""
        config = self.config_service.current()
        client = self.ollama_client or OllamaClient(
            host=config.endpoint,
            model=config.model_name,
            timeout=config.timeout_seconds,
            temperature=config.temperature,
            token_limit=config.token_limit,
        )
        context = self.context_builder.build(question, retrieval, user=user)
        prompt = self.prompt_template.build(question, context)
        status = "generated"
        warning = ""
        started = time.perf_counter()
        try:
            if "options" in signature(client.generate_response).parameters:
                ai_response = client.generate_response(prompt, options=config.ollama_options())
            else:
                ai_response = client.generate_response(prompt)
            answer = ai_response.answer
            model = ai_response.model
            response_time_ms = ai_response.response_time_ms
        except OllamaClientError:
            answer = fallback_builder(question, retrieval) if fallback_builder else ""
            model = config.model_name
            response_time_ms = int((time.perf_counter() - started) * 1000)
            status = "fallback"
            warning = "Ollama is unavailable; returned source-based fallback answer."

        if self.answer_transformer is not None:
            answer = self.answer_transformer(answer, retrieval, status)

        evaluation = self.evaluator.evaluate(answer, retrieval)
        warning = warning or evaluation["hallucination_warning"]
        self.logger.log(
            user=user,
            question=question,
            retrieval=retrieval,
            model=model,
            response_time_ms=response_time_ms,
            confidence=evaluation["confidence"],
            warning=warning,
            status=status,
        )
        return {
            "answer": answer,
            "sources": retrieval.get("sources", []),
            "confidence": evaluation["confidence"],
            "warning": warning,
            "model": model,
            "provider": "ollama-local" if status == "generated" else "source-fallback",
            "response_time_ms": response_time_ms,
            "generation_status": status,
            "source_relevance_score": evaluation["source_relevance_score"],
            "hallucination_warning": evaluation["hallucination_warning"],
        }


