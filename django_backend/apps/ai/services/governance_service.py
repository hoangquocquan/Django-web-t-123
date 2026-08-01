"""Governance V2: normalize, policy, redaction, rate limit và audit versioning."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass

from django.conf import settings

from apps.ai.models import AIGovernanceEvent
from apps.ai.services.normalization_service import AIInputNormalizer
from apps.ai.services.policy_service import AIPolicyContext, AIPolicyEngine
from apps.ai.services.rate_limit_service import AIRateLimiter, DjangoCacheRateLimitBackend
from apps.ai.services.redaction_service import AIRedactionService


class AIGovernanceError(RuntimeError):
    def __init__(self, code, message, status_code=400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class AIGovernanceDecision:
    allowed: bool
    decision: str
    reason: str = ""
    correlation_id: str = ""
    policy_version: str = ""


class AIGovernanceService:
    """Chạy toàn bộ kiểm soát trước khi request được gửi đến model hoặc tool."""

    def __init__(
        self,
        cache_backend=None,
        rate_limiter=None,
        normalizer=None,
        policy_engine=None,
        redactor=None,
    ):
        self.normalizer = normalizer or AIInputNormalizer()
        self.policy_engine = policy_engine or AIPolicyEngine(
            version=getattr(settings, "AI_POLICY_VERSION", "ai-policy-v2.0")
        )
        self.redactor = redactor or AIRedactionService()
        self.rate_limiter = rate_limiter or AIRateLimiter(
            backend=DjangoCacheRateLimitBackend(cache_backend) if cache_backend is not None else None
        )
        self.max_input_chars = int(getattr(settings, "AI_MAX_INPUT_CHARS", 12000))

    def enforce(
        self,
        *,
        user,
        endpoint,
        action,
        text="",
        limit=None,
        metadata=None,
        ip_address="",
        organization_id="",
        module="",
        tool="",
        request_source="api",
    ):
        original = str(text or "")
        correlation_id = str(uuid.uuid4())
        context = AIPolicyContext(
            user_email=getattr(user, "email", "") or "",
            role=getattr(getattr(user, "role", None), "name", "") or "",
            organization_id=str(organization_id or ""),
            module=module or endpoint.split("/", 1)[0],
            endpoint=endpoint,
            action=action,
            tool=tool,
            request_source=request_source,
            policy_version=getattr(settings, "AI_POLICY_VERSION", "ai-policy-v2.0"),
        )
        normalized = self.normalizer.normalize(original)
        normalized_hash = self.hash_text(normalized.normalized)
        safe_metadata, redaction_summary = self.redactor.redact_value(metadata or {})

        if len(original) > self.max_input_chars:
            self.record(
                context=context,
                decision=AIGovernanceEvent.DECISION_BLOCKED,
                reason="AI request exceeds the configured size limit.",
                request_hash=normalized_hash,
                metadata=safe_metadata,
                matched_rule_ids=["INPUT-SIZE-001"],
                redaction_summary=redaction_summary,
                correlation_id=correlation_id,
            )
            raise AIGovernanceError("ai_input_too_large", "AI request exceeds the configured size limit.", 413)

        rate_results = self.rate_limiter.enforce(
            context=context,
            ip_address=ip_address,
            limit=limit,
        )
        exceeded = next((result for result in rate_results if not result.allowed), None)
        if exceeded:
            self.record(
                context=context,
                decision=AIGovernanceEvent.DECISION_RATE_LIMITED,
                reason="Rate limit exceeded.",
                request_hash=normalized_hash,
                metadata={
                    **safe_metadata,
                    "rate_limit_scope": exceeded.key_scope,
                    "rate_limit_backend": exceeded.backend,
                    "limit": exceeded.limit,
                    "window_seconds": self.rate_limiter.window_seconds,
                },
                matched_rule_ids=["RATE-LIMIT-001"],
                redaction_summary=redaction_summary,
                correlation_id=correlation_id,
            )
            raise AIGovernanceError("ai_rate_limited", "AI request rate limit exceeded.", 429)

        policy = self.policy_engine.evaluate(normalized.scan_text, context)
        if not policy["allowed"]:
            self.record(
                context=context,
                decision=AIGovernanceEvent.DECISION_BLOCKED,
                reason=policy["message"],
                request_hash=normalized_hash,
                metadata={
                    **safe_metadata,
                    "normalization": {
                        "zero_width_removed": normalized.zero_width_removed,
                        "spaced_characters_collapsed": normalized.spaced_characters_collapsed,
                    },
                },
                matched_rule_ids=policy["matched_rule_ids"],
                redaction_summary=redaction_summary,
                correlation_id=correlation_id,
            )
            raise AIGovernanceError("ai_policy_blocked", policy["message"], 400)

        self.record(
            context=context,
            decision=AIGovernanceEvent.DECISION_ALLOWED,
            reason="Policy checks passed.",
            request_hash=normalized_hash,
            metadata=safe_metadata,
            matched_rule_ids=[],
            redaction_summary=redaction_summary,
            correlation_id=correlation_id,
        )
        return AIGovernanceDecision(
            allowed=True,
            decision=AIGovernanceEvent.DECISION_ALLOWED,
            correlation_id=correlation_id,
            policy_version=context.policy_version,
        )

    def prompt_safety_reason(self, text):
        """API tương thích cho test cũ, dùng chung policy V2."""
        normalized = self.normalizer.normalize(text)
        context = AIPolicyContext(policy_version=self.policy_engine.version)
        result = self.policy_engine.evaluate(normalized.scan_text, context)
        return "" if result["allowed"] else result["message"]

    def rate_key(self, user, endpoint):
        user_identity = getattr(user, "email", "") or f"user:{getattr(user, 'id', 'anonymous')}"
        return f"ai-rate:v2:user:{user_identity}:{endpoint}"

    @staticmethod
    def hash_text(text):
        normalized = " ".join(str(text or "").split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest() if normalized else ""

    def record(
        self,
        *,
        context,
        decision,
        reason,
        request_hash,
        metadata,
        matched_rule_ids,
        redaction_summary,
        correlation_id,
    ):
        return AIGovernanceEvent.objects.create(
            user_email=context.user_email,
            role_name=context.role,
            organization_id=context.organization_id,
            module=context.module,
            endpoint=context.endpoint,
            action=context.action,
            tool_name=context.tool,
            request_source=context.request_source,
            decision=decision,
            reason=reason[:240],
            request_hash=request_hash,
            policy_version=context.policy_version,
            matched_rule_ids=matched_rule_ids,
            redaction_summary=redaction_summary,
            correlation_id=correlation_id,
            metadata=metadata or {},
        )
