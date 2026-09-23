"""Public knowledge assistant isolated from internal business context."""

from __future__ import annotations

import re
import unicodedata
import hashlib

from django.conf import settings
from django.core.exceptions import PermissionDenied

from apps.ai.models import AIRequestLog
from apps.knowledge.services.access_policy import KnowledgeAccessPolicy
from apps.knowledge.models import KnowledgeAssistantLog
from apps.knowledge.services.rag_pipeline import (
    RagGenerationPipeline,
    RagPromptTemplate,
)
from apps.knowledge.services.search_service import KnowledgeSearchService


class PublicRagContextBuilder:
    """Build RAG context from approved public documents and nothing else."""

    def build(self, question, retrieval, user=None):
        del question, user
        ranked_results = sorted(
            retrieval.get("results", []),
            key=lambda result: result.get("score", 0),
            reverse=True,
        )
        context_lines = []
        for index, result in enumerate(ranked_results, start=1):
            document = result.get("document") or {}
            if document.get("permission_level") != "public":
                continue
            context_lines.append(
                f"[{index}] {document.get('title', '')} | "
                f"relevance={round(result.get('score', 0), 4)}: "
                f"{(result.get('chunk') or {}).get('content', '')}"
            )
        return {
            "knowledge_context": "\n".join(context_lines),
            "business_context": "Unavailable to the public assistant.",
            "ranked_results": ranked_results,
        }


class PublicAIRequestLogService:
    """Audit public responses with an accurate provider classification."""

    def log(self, *, user, question, retrieval, model, response_time_ms, confidence, warning, status):
        del user
        normalized_question = " ".join(str(question or "").split())
        provider = "ollama-local" if status == "generated" else "source-fallback"
        if status in {"blocked_policy", "fixed_public_safety"}:
            provider = "policy-guard"
        return AIRequestLog.objects.create(
            request_type="public_knowledge",
            user_email="",
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
            provider=provider,
            response_time_ms=response_time_ms,
            confidence=confidence,
            warning=warning,
            status=status,
        )


class PublicKnowledgeAssistantService:
    """Answer anonymous questions using public documents only."""

    def __init__(self, search_service=None, generation_pipeline=None):
        self.search_service = search_service or KnowledgeSearchService()
        self.audit_logger = PublicAIRequestLogService()
        self.generation_pipeline = generation_pipeline or RagGenerationPipeline(
            context_builder=PublicRagContextBuilder(),
            logger=self.audit_logger,
            answer_transformer=self._ensure_source_citation,
        )

    def answer(self, question, limit=5):
        """Apply deterministic public policy before source-grounded generation."""
        if not getattr(settings, "PUBLIC_AI_ENABLED", False):
            raise PermissionDenied("Public AI is not released.")
        question = " ".join(str(question or "").split())
        policy = self.policy_response(question)
        if policy:
            return self._fixed_result(question, **policy)

        raw_retrieval = self.search_service.search(question, limit=limit, user=None)
        retrieval = self._public_only(raw_retrieval)
        if not retrieval["sources"]:
            return self._fixed_result(
                question,
                rule_id="PUBLIC-NO-CONTEXT",
                answer=(
                    "Hiện chưa có tài liệu công khai đã được phê duyệt để trả lời "
                    "câu hỏi này. Chatbot không truy xuất tài liệu nội bộ."
                ),
                status="blocked_no_public_context",
                provider="source-fallback",
                warning="No approved public source context was available; Ollama was not called.",
                confidence=0.0,
            )

        result = self.generation_pipeline.generate(
            question,
            retrieval,
            user=None,
            fallback_builder=self._fallback_answer,
        )
        if not KnowledgeAccessPolicy().sources_still_readable(result.get("sources", []), None):
            return self._fixed_result(
                question, rule_id="PUBLIC-SOURCE-REVOKED",
                answer="Nguồn công khai đã thay đổi; không thể trả lời từ nguồn này.",
                status="blocked_no_public_context", provider="source-fallback",
                warning="Public source authorization changed during generation.", confidence=0.0,
            )
        result.update(
            {
                "policy_rule_id": "PUBLIC-SOURCE-GROUNDED",
                "public_scope": True,
                "business_context_used": False,
                "publication_state": self._publication_state(),
            }
        )
        self._audit_answer(question, result)
        return result

    def policy_response(self, question):
        """Return a fixed public response for sensitive or commitment requests."""
        normalized = self._normalize(question)
        if re.search(
            r"(bao gia|du lieu|don hang).{0,50}khach hang.{0,20}(khac|another)|"
            r"khach hang.{0,50}(bao gia|du lieu|don hang)",
            normalized,
        ):
            return {
                "rule_id": "PUBLIC-PRIVACY-CUSTOMER",
                "answer": (
                    "Tôi không thể cung cấp báo giá, đơn hàng hoặc dữ liệu riêng "
                    "của khách hàng khác."
                ),
                "status": "blocked_policy",
                "provider": "policy-guard",
                "warning": "Customer-private information is not available to the public chatbot.",
                "confidence": 1.0,
            }
        if re.search(
            r"tai lieu.{0,20}(noi bo|internal|restricted)|"
            r"(doc|xem|truy xuat).{0,30}(noi bo|internal|restricted)",
            normalized,
        ):
            return {
                "rule_id": "PUBLIC-INTERNAL-DOCUMENT",
                "answer": (
                    "Tôi không thể truy cập hoặc cung cấp tài liệu internal/restricted. "
                    "Chatbot công khai chỉ được sử dụng tài liệu public đã được phê duyệt."
                ),
                "status": "blocked_policy",
                "provider": "policy-guard",
                "warning": "Internal and restricted documents are excluded from public retrieval.",
                "confidence": 1.0,
            }
        if re.search(
            r"\b(gia|price|cost).{0,40}(bao nhieu|how much)|"
            r"(bao nhieu|how much).{0,40}\b(gia|price|cost)\b",
            normalized,
        ):
            return {
                "rule_id": "PUBLIC-NO-PRICE-COMMITMENT",
                "answer": (
                    "Chatbot không cung cấp mức giá hoặc báo giá chính thức. Giá cần "
                    "được nhân viên phụ trách xác nhận sau khi xem bản vẽ, vật liệu, "
                    "số lượng và yêu cầu kỹ thuật cụ thể."
                ),
                "status": "fixed_public_safety",
                "provider": "policy-guard",
                "warning": "No price was estimated or committed.",
                "confidence": 1.0,
            }
        if re.search(
            r"giao.{0,30}\b\d+[,.]?\d*\s*(ngay|gio|day|hour)|"
            r"dung sai.{0,30}\d|tolerance.{0,30}\d|"
            r"cam ket.{0,30}(tien do|giao|dung sai)",
            normalized,
        ):
            return {
                "rule_id": "PUBLIC-NO-TECHNICAL-COMMITMENT",
                "answer": (
                    "Chatbot không thể cam kết tiến độ giao hàng hoặc dung sai cụ thể. "
                    "Khả năng thực hiện phải được bộ phận kỹ thuật thẩm định từ bản vẽ, "
                    "vật liệu, số lượng và yêu cầu kiểm tra trước khi nhân viên xác nhận."
                ),
                "status": "fixed_public_safety",
                "provider": "policy-guard",
                "warning": "No delivery schedule or tolerance was committed.",
                "confidence": 1.0,
            }
        return None

    def _public_only(self, retrieval):
        """Defensively discard any non-public result returned by a dependency."""
        results = [
            result
            for result in retrieval.get("results", [])
            if self._approved_public_result(result)
        ]
        public_results = {
            (result.get("document") or {}).get("id"): result for result in results
        }
        sources = [
            {
                "id": source.get("id"),
                "title": source.get("title", ""),
                "permission_level": "public",
                "relevance_score": source.get("relevance_score", 0),
                "version": public_results[source.get("id")]["document"].get("version"),
                "revision_date": public_results[source.get("id")]["document"].get("revision_date"),
                "revision_id": (public_results[source.get("id")].get("chunk") or {}).get("revision_id"),
                "section": (public_results[source.get("id")].get("chunk") or {}).get("section"),
                "page": (public_results[source.get("id")].get("chunk") or {}).get("page"),
            }
            for source in retrieval.get("sources", [])
            if source.get("permission_level") == "public"
            and source.get("id") in public_results
        ]
        confidence = max(
            (float(result.get("score", 0) or 0) for result in results),
            default=0.0,
        )
        return {
            "results": results,
            "sources": sources,
            "confidence": round(confidence, 4),
        }

    @staticmethod
    def _approved_public_result(result):
        doc = result.get("document") or {}
        return (
            doc.get("permission_level") == "public"
            and doc.get("status") in {"APPROVED", "INDEXED"}
            and doc.get("active_version") is True
            and doc.get("ai_public_approved") is True
            and doc.get("approved_version") == doc.get("version")
            and bool((result.get("chunk") or {}).get("revision_id"))
        )

    def _fixed_result(
        self,
        question,
        *,
        rule_id,
        answer,
        status,
        provider,
        warning,
        confidence,
    ):
        retrieval = {"results": [], "sources": [], "confidence": confidence}
        model = getattr(settings, "OLLAMA_MODEL", "local-model")
        self.audit_logger.log(
            user=None,
            question=question,
            retrieval=retrieval,
            model=model,
            response_time_ms=0,
            confidence=confidence,
            warning=warning,
            status=status,
        )
        result = {
            "answer": answer,
            "sources": [],
            "confidence": confidence,
            "warning": warning,
            "model": model,
            "provider": provider,
            "response_time_ms": 0,
            "generation_status": status,
            "source_relevance_score": 0.0,
            "hallucination_warning": warning,
            "policy_rule_id": rule_id,
            "public_scope": True,
            "business_context_used": False,
            "publication_state": self._publication_state(),
        }
        self._audit_answer(question, result)
        return result

    def _audit_answer(self, question, result):
        KnowledgeAssistantLog.objects.create(
            question="",
            answer="",
            sources=[{"id": source.get("id"), "version": source.get("version")} for source in result.get("sources", [])],
            confidence=result.get("confidence", 0),
            warning=result.get("warning", ""),
            user_email="",
        )

    @staticmethod
    def _fallback_answer(question, retrieval):
        del question
        titles = ", ".join(
            source.get("title", "") for source in retrieval.get("sources", [])
        )
        return (
            f"Có tài liệu công khai liên quan: {titles}. "
            "Vui lòng kiểm tra nguồn được trích dẫn."
        )

    @staticmethod
    def _ensure_source_citation(answer, retrieval, status):
        """Append deterministic public source titles when Ollama omits them."""
        if status != "generated":
            return answer
        titles = [
            str(source.get("title") or "").strip()
            for source in retrieval.get("sources", [])
            if str(source.get("title") or "").strip()
        ]
        if not titles or any(title in answer for title in titles):
            return answer
        return f"{answer.rstrip()}\n\nNguồn: {', '.join(titles)}."

    @staticmethod
    def _normalize(value):
        normalized = unicodedata.normalize("NFKD", str(value or "").casefold())
        without_marks = "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )
        return " ".join(without_marks.replace("đ", "d").split())

    @staticmethod
    def _publication_state():
        if getattr(settings, "PUBLIC_CHATBOT_DEMO_ISOLATED", False):
            return "isolated_demo_unapproved"
        return "public_sources_only"


def build_public_prompt(question, retrieval):
    """Expose the public prompt builder for focused safety tests."""
    context = PublicRagContextBuilder().build(question, retrieval)
    return RagPromptTemplate().build(question, context)

