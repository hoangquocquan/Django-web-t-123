"""Grounded Ollama synthesis for sales summaries and draft emails."""

from __future__ import annotations

import json
import logging
import re

from django.conf import settings

from apps.ai.services.ollama_client import OllamaClient, OllamaClientError


logger = logging.getLogger(__name__)


class SalesSynthesisValidationError(ValueError):
    """Raised when model output is unsafe or violates the response contract."""


class GroundedSalesSynthesisService:
    """Generate advisory sales content while preserving deterministic business facts."""

    REQUIRED_FIELDS = {
        "summary",
        "reasoning_summary",
        "recommended_next_steps",
        "draft_email",
        "risks",
        "source_ids",
        "human_approval_required",
        "autonomous_action",
    }
    BANNED_ACTIONS = (
        "email sent",
        "sent the email",
        "crm updated",
        "quotation approved",
        "discount applied",
        "order created",
        "pipeline moved",
        "đã gửi email",
        "đã cập nhật crm",
        "đã duyệt báo giá",
        "đã tạo đơn hàng",
    )

    def __init__(self, client=None, max_attempts=None):
        """Allow deterministic client injection and bounded content retries in tests."""
        self.client = client or OllamaClient(retries=0)
        self.max_attempts = int(max_attempts or getattr(settings, "AI_SALES_SYNTHESIS_ATTEMPTS", 2))

    def synthesize(self, facts, task="lead_analysis"):
        """Return validated Ollama JSON or an explicitly marked deterministic fallback."""
        if not getattr(settings, "AI_SALES_OLLAMA_ENABLED", True):
            return self._fallback(facts, task, "Ollama synthesis is disabled in this environment.")

        prompt = self._prompt(facts, task)
        errors = []
        for attempt in range(max(1, self.max_attempts)):
            try:
                response = self.client.generate_response(prompt, response_format="json")
                payload = self._parse_json(response.answer)
                self.validate(payload, facts)
                return {
                    **payload,
                    "generation_mode": "ollama",
                    "model": response.model,
                    "response_time_ms": response.response_time_ms,
                    "validation_errors": [],
                }
            except (OllamaClientError, SalesSynthesisValidationError) as exc:
                errors.append(str(exc))
                prompt = self._repair_prompt(prompt, str(exc))

        logger.warning("AI Sales synthesis used fallback; prompt and PII were not logged: %s", errors[-1])
        return self._fallback(facts, task, errors[-1] if errors else "Unknown synthesis failure.")

    def validate(self, payload, facts):
        """Reject malformed, ungrounded, autonomous, or action-claiming model output."""
        if not isinstance(payload, dict):
            raise SalesSynthesisValidationError("Model output must be a JSON object.")
        missing = self.REQUIRED_FIELDS.difference(payload)
        if missing:
            raise SalesSynthesisValidationError(f"Missing required fields: {', '.join(sorted(missing))}.")
        if not isinstance(payload["summary"], str) or not payload["summary"].strip():
            raise SalesSynthesisValidationError("summary must be a non-empty string.")
        for field in ("reasoning_summary", "recommended_next_steps", "risks", "source_ids"):
            if not isinstance(payload[field], list):
                raise SalesSynthesisValidationError(f"{field} must be a list.")
        draft = payload.get("draft_email")
        if not isinstance(draft, dict) or not isinstance(draft.get("subject"), str) or not isinstance(draft.get("body"), str):
            raise SalesSynthesisValidationError("draft_email requires string subject and body.")
        if payload["human_approval_required"] is not True or payload["autonomous_action"] is not False:
            raise SalesSynthesisValidationError("Human approval and non-autonomous output are mandatory.")
        if self._contains_score_key(payload):
            raise SalesSynthesisValidationError("The language model cannot return or modify a lead score.")

        allowed_sources = {source.get("id") for source in facts.get("knowledge_sources", [])}
        if any(source_id not in allowed_sources for source_id in payload["source_ids"]):
            raise SalesSynthesisValidationError("Model output references an unknown knowledge source.")

        rendered = json.dumps(payload, ensure_ascii=False).casefold()
        if any(action in rendered for action in self.BANNED_ACTIONS):
            raise SalesSynthesisValidationError("Model output claims a prohibited autonomous action.")
        self._validate_pipeline_claims(rendered, facts)
        return payload

    def _validate_pipeline_claims(self, rendered, facts):
        """Reject common hallucinated lead outcomes that contradict the database status."""
        current_status = str(facts.get("lead_facts", {}).get("status", "")).casefold()
        status_claims = {
            "won": (r"\bwon\b", "đã thắng", "đã chốt"),
            "lost": (r"\blost\b", "đã mất lead", "thất bại"),
            "meeting": (r"\bmeeting (?:is )?scheduled\b", "đã đặt lịch họp"),
            "quotation": (r"\bquotation (?:was |is )?(?:created|sent)\b", "đã gửi báo giá"),
            "negotiation": (r"\bin negotiation\b", "đang đàm phán"),
        }
        for claimed_status, patterns in status_claims.items():
            if claimed_status == current_status:
                continue
            if any(re.search(pattern, rendered) for pattern in patterns):
                raise SalesSynthesisValidationError(
                    f"Model output contradicts deterministic lead status '{current_status or 'unknown'}'."
                )

    def _prompt(self, facts, task):
        """Create a strict source-grounded JSON prompt for the local model."""
        return (
            "You are a cautious B2B sales analyst for MEC Precision. Use ONLY the JSON facts below. "
            "Do not invent facts or source IDs. Never change or repeat the lead score. Never claim that an email "
            "was sent, CRM was updated, a quotation was approved, a discount was applied, an order was created, "
            "or a pipeline stage was changed. Return one JSON object only with exactly these fields: summary "
            "(string), reasoning_summary (string array), recommended_next_steps (string array), draft_email "
            "({subject:string, body:string}), risks (string array), source_ids (array using only IDs present in "
            "knowledge_sources), human_approval_required (true), autonomous_action (false). "
            f"Task: {task}. Facts: {json.dumps(facts, ensure_ascii=False, default=str)}"
        )

    def _repair_prompt(self, original_prompt, error_message):
        """Request one bounded correction without including operational secrets."""
        return f"{original_prompt}\nYour previous output was rejected: {error_message} Return corrected JSON only."

    def _parse_json(self, raw):
        """Parse plain JSON or a single fenced JSON block."""
        text = str(raw or "").strip()
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            text = fenced.group(1)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise SalesSynthesisValidationError("Model output is not valid JSON.") from exc

    def _contains_score_key(self, value):
        """Recursively prevent the generative layer from shadowing deterministic scores."""
        if isinstance(value, dict):
            return any(str(key).casefold() in {"score", "lead_score"} or self._contains_score_key(item) for key, item in value.items())
        if isinstance(value, list):
            return any(self._contains_score_key(item) for item in value)
        return False

    def _fallback(self, facts, task, reason):
        """Create useful, deterministic content while clearly reporting Ollama failure."""
        lead = facts.get("lead_facts", {})
        sales = facts.get("sales_facts", {})
        company = lead.get("company") or "khách hàng"
        contact = lead.get("contact_person") or "Anh/Chị"
        product = sales.get("product_interest") or "giải pháp gia công chính xác"
        source_ids = [source.get("id") for source in facts.get("knowledge_sources", []) if source.get("id") is not None]
        return {
            "summary": f"{company} cần được nhân viên xác minh nhu cầu kỹ thuật trước khi tư vấn.",
            "reasoning_summary": ["Kết quả được tạo từ dữ liệu CRM, Sales và nguồn kiến thức đã truy xuất."],
            "recommended_next_steps": ["Xác minh bản vẽ, vật liệu, số lượng, dung sai và thời hạn giao hàng."],
            "draft_email": {
                "subject": f"MEC Precision - Trao đổi về {product}",
                "body": (
                    f"Xin chào {contact},\n\nCảm ơn {company} đã quan tâm đến {product}. "
                    "Vui lòng gửi bản vẽ, vật liệu, số lượng và thời hạn để kỹ sư của chúng tôi đánh giá.\n\n"
                    "Trân trọng,\nMEC Precision VIETNAM"
                ),
            },
            "risks": ["Ollama không tạo được kết quả hợp lệ; nhân viên phải kiểm tra toàn bộ nội dung."],
            "source_ids": source_ids,
            "human_approval_required": True,
            "autonomous_action": False,
            "generation_mode": "fallback",
            "model": "",
            "response_time_ms": 0,
            "validation_errors": [reason],
            "task": task,
        }
