"""Enterprise governance checks for AI endpoints."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache

from apps.ai.models import AIGovernanceEvent


class AIGovernanceError(RuntimeError):
    """Raised when an AI request violates a governance policy."""

    def __init__(self, code, message, status_code=400):
        """Store API-safe error data."""
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class AIGovernanceDecision:
    """Serializable result for one AI policy decision."""

    allowed: bool
    decision: str
    reason: str = ""


class AIGovernanceService:
    """Apply rate limits, prompt safety, and audit logging before AI execution."""

    blocked_patterns = (
        r"\bignore\s+(all\s+)?previous\s+instructions\b",
        r"\breveal\s+(system|developer)\s+prompt\b",
        r"\bshow\s+.*\b(api[_ -]?key|secret|password|token)\b",
        r"\bdelete\s+.*\b(database|customer|quotation|order)\b",
        r"\bauto(?:matically)?\s+(send|approve|merge|deploy)\b",
        r"\bshutdown\s+(legacy|production|server)\b",
    )

    def __init__(self, cache_backend=None):
        """Allow tests to inject a cache-like object."""
        self.cache = cache_backend or cache
        self.window_seconds = int(getattr(settings, "AI_RATE_LIMIT_WINDOW_SECONDS", 60))
        self.default_limit = int(getattr(settings, "AI_RATE_LIMIT_PER_USER", 30))

    def enforce(self, *, user, endpoint, action, text="", limit=None, metadata=None):
        """Validate one request and write a governance audit event."""
        request_hash = self.hash_text(text)
        limit = int(limit or self.default_limit)
        rate_key = self.rate_key(user, endpoint)
        current = self.cache.get(rate_key, 0)
        if current >= limit:
            self.record(
                user=user,
                endpoint=endpoint,
                action=action,
                decision=AIGovernanceEvent.DECISION_RATE_LIMITED,
                reason="Rate limit exceeded.",
                request_hash=request_hash,
                metadata={"limit": limit, "window_seconds": self.window_seconds, **(metadata or {})},
            )
            raise AIGovernanceError("ai_rate_limited", "AI request rate limit exceeded.", status_code=429)

        safety_reason = self.prompt_safety_reason(text)
        if safety_reason:
            self.increment_rate(rate_key)
            self.record(
                user=user,
                endpoint=endpoint,
                action=action,
                decision=AIGovernanceEvent.DECISION_BLOCKED,
                reason=safety_reason,
                request_hash=request_hash,
                metadata=metadata or {},
            )
            raise AIGovernanceError("ai_policy_blocked", safety_reason, status_code=400)

        self.increment_rate(rate_key)
        self.record(
            user=user,
            endpoint=endpoint,
            action=action,
            decision=AIGovernanceEvent.DECISION_ALLOWED,
            reason="Policy checks passed.",
            request_hash=request_hash,
            metadata=metadata or {},
        )
        return AIGovernanceDecision(allowed=True, decision=AIGovernanceEvent.DECISION_ALLOWED)

    def prompt_safety_reason(self, text):
        """Return a block reason when prompt text asks for unsafe behavior."""
        normalized = " ".join(str(text or "").lower().split())
        for pattern in self.blocked_patterns:
            if re.search(pattern, normalized):
                return "Prompt blocked by AI safety policy."
        return ""

    def rate_key(self, user, endpoint):
        """Build a per-user, per-endpoint rate key."""
        user_identity = getattr(user, "email", "") or f"user:{getattr(user, 'id', 'anonymous')}"
        return f"ai-rate:{endpoint}:{user_identity}"

    def increment_rate(self, key):
        """Increment a cache counter with a short TTL."""
        added = self.cache.add(key, 1, timeout=self.window_seconds)
        if not added:
            try:
                self.cache.incr(key)
            except ValueError:
                self.cache.set(key, 1, timeout=self.window_seconds)

    @staticmethod
    def hash_text(text):
        """Hash request text so audit does not store full sensitive prompts."""
        normalized = " ".join(str(text or "").split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest() if normalized else ""

    def record(self, *, user, endpoint, action, decision, reason, request_hash, metadata):
        """Persist a safe governance audit event."""
        return AIGovernanceEvent.objects.create(
            user_email=getattr(user, "email", "") or "",
            endpoint=endpoint,
            action=action,
            decision=decision,
            reason=reason[:240],
            request_hash=request_hash,
            metadata=metadata or {},
        )

