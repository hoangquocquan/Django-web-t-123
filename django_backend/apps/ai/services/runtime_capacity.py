"""Distributed capacity control for local AI inference."""

from __future__ import annotations

import uuid
from contextlib import contextmanager

from django.conf import settings


class AIRuntimeBusyError(RuntimeError):
    """Raised when the bounded local inference queue has no free slot."""


class RedisCapacityBackend:
    """Use Redis sorted sets so every web worker shares the same capacity limit."""

    ACQUIRE = """
local now = tonumber(ARGV[1])
local expires = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
if redis.call('ZCARD', KEYS[1]) >= limit then return 0 end
redis.call('ZADD', KEYS[1], expires, ARGV[4])
redis.call('EXPIRE', KEYS[1], math.ceil((expires-now)/1000)+1)
return 1
""".strip()

    def __init__(self, redis_url=None, client=None):
        if client is None:
            import redis

            client = redis.Redis.from_url(
                redis_url or getattr(settings, "REDIS_URL", ""), decode_responses=True
            )
        self.client = client
        self.acquire_script = client.register_script(self.ACQUIRE)

    def acquire(self, key, token, limit, lease_ms, now_ms):
        return bool(
            self.acquire_script(
                keys=[key], args=[now_ms, now_ms + lease_ms, limit, token]
            )
        )

    def release(self, key, token):
        self.client.zrem(key, token)


class AIRuntimeCapacity:
    """Fail closed when local inference concurrency exceeds configured capacity."""

    def __init__(self, backend=None, limit=None, lease_seconds=None, clock=None):
        import time

        self.backend = backend or RedisCapacityBackend()
        self.limit = max(
            1, int(limit or getattr(settings, "AI_OLLAMA_MAX_CONCURRENCY", 2))
        )
        self.lease_ms = max(
            1000,
            int(lease_seconds or getattr(settings, "AI_OLLAMA_LEASE_SECONDS", 120))
            * 1000,
        )
        self.clock = clock or time.time

    @contextmanager
    def slot(self, purpose="generation"):
        """Acquire one distributed slot and always release it after the request."""
        token = str(uuid.uuid4())
        key = f"ai-runtime:capacity:{purpose}"
        acquired = self.backend.acquire(
            key, token, self.limit, self.lease_ms, int(self.clock() * 1000)
        )
        if not acquired:
            raise AIRuntimeBusyError("Local AI runtime is at capacity; retry later.")
        try:
            yield
        finally:
            self.backend.release(key, token)
