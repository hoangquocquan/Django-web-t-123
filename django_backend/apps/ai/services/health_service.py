"""Health management for the local Ollama runtime."""

from __future__ import annotations

import logging

from apps.ai.services.model_config import AIModelConfigService
from apps.ai.services.ollama_client import OllamaClient, OllamaClientError


logger = logging.getLogger(__name__)


class OllamaHealthService:
    """Check local Ollama availability and selected model status."""

    def __init__(self, client=None, config_service=None):
        """Allow tests to inject a fake client/config."""
        self.config_service = config_service or AIModelConfigService()
        self.client = client

    def check(self):
        """Return health payload without exposing prompts or secrets."""
        config = self.config_service.current()
        client = self.client or OllamaClient(
            host=config.endpoint,
            model=config.model_name,
            timeout=config.timeout_seconds,
        )
        try:
            health = client.health_check()
        except OllamaClientError as exc:
            logger.warning("Ollama health check failed: %s", exc)
            return {
                "status": "unavailable",
                "available": False,
                "model": config.model_name,
                "model_available": False,
                "endpoint": config.endpoint,
                "error": str(exc),
            }

        model_available = bool(health.get("model_available"))
        return {
            "status": "ready" if model_available else "model_missing",
            "available": True,
            "model": config.model_name,
            "model_available": model_available,
            "endpoint": config.endpoint,
            "models": health.get("models", []),
        }

