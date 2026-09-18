"""Rate limit nhiều chiều với Redis atomic và local development fallback."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    count: int
    limit: int
    backend: str
    key_scope: str


class DjangoCacheRateLimitBackend:
    """Fallback local; phù hợp test/dev nhưng không restart-safe hoặc multi-worker-safe."""

    backend_name = "django-cache-development-fallback"

    def __init__(self, cache_backend=None):
        self.cache = cache_backend or cache

    def increment(self, key, window_seconds):
        added = self.cache.add(key, 1, timeout=window_seconds)
        if added:
            return 1
        try:
            return int(self.cache.incr(key))
        except ValueError:
            self.cache.set(key, 1, timeout=window_seconds)
            return 1

    def health_check(self):
        return {
            "available": True,
            "backend": self.backend_name,
            "distributed": False,
            "warning": "Development fallback is not restart-safe or multi-worker-safe.",
        }


class RedisRateLimitBackend:
    """Redis backend dùng Lua để INCR và EXPIRE trong một thao tác atomic."""

    backend_name = "redis-atomic"
    LUA_INCREMENT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
""".strip()

    def __init__(self, redis_url=None, client=None):
        self.redis_url = redis_url or getattr(settings, "REDIS_URL", "")
        if client is None:
            try:
                import redis
            except ImportError as exc:
                raise RuntimeError("Redis package is required for distributed AI rate limiting.") from exc
            client = redis.Redis.from_url(self.redis_url, decode_responses=True)
        self.client = client
        self.increment_script = self.client.register_script(self.LUA_INCREMENT)

    def increment(self, key, window_seconds):
        return int(self.increment_script(keys=[key], args=[int(window_seconds)]))

    def health_check(self):
        try:
            available = bool(self.client.ping())
        except Exception as exc:
            return {"available": False, "backend": self.backend_name, "distributed": True, "error": str(exc)}
        return {"available": available, "backend": self.backend_name, "distributed": True}


class AIRateLimiter:
    """Áp giới hạn theo user, IP, organization, endpoint và action."""

    def __init__(self, backend=None, window_seconds=None, default_limit=None):
        self.window_seconds = int(window_seconds or getattr(settings, "AI_RATE_LIMIT_WINDOW_SECONDS", 60))
        self.default_limit = int(default_limit or getattr(settings, "AI_RATE_LIMIT_PER_USER", 30))
        if backend is not None:
            self.backend = backend
        elif getattr(settings, "AI_REDIS_RATE_LIMIT_ENABLED", False) and getattr(settings, "REDIS_URL", ""):
            self.backend = RedisRateLimitBackend()
        else:
            self.backend = DjangoCacheRateLimitBackend()
            logger.warning("AI rate limiting uses development cache fallback; configure Redis for multi-worker runtime.")

    def enforce(self, *, context, ip_address="", limit=None):
        selected_limit = int(limit or self.default_limit)
        subject = context.user_email or ip_address or "anonymous"
        dimensions = {
            "endpoint": f"{subject}:{context.endpoint or 'unknown'}",
            "action": f"{subject}:{context.action or 'unknown'}",
        }
        if context.user_email:
            dimensions["user"] = context.user_email
        if ip_address:
            dimensions["ip"] = ip_address
        if context.organization_id:
            dimensions["organization"] = context.organization_id
        results = []
        for scope, value in dimensions.items():
            key = f"ai-rate:v2:{scope}:{value}"
            count = self.backend.increment(key, self.window_seconds)
            results.append(
                RateLimitResult(
                    allowed=count <= selected_limit,
                    count=count,
                    limit=selected_limit,
                    backend=self.backend.backend_name,
                    key_scope=scope,
                )
            )
        return results
