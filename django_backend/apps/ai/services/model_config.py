"""AI model configuration for local Ollama inference."""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True)
class AIModelConfig:
    """Cau hinh model local dung cho RAG va AI Sales."""

    model_name: str
    temperature: float
    token_limit: int
    timeout_seconds: int
    endpoint: str

    def ollama_options(self):
        """Chuyen cau hinh sang object `options` cua Ollama."""
        return {
            "temperature": self.temperature,
            "num_predict": self.token_limit,
        }


class AIModelConfigService:
    """Doc cau hinh AI tu Django settings/env."""

    def current(self):
        """Return the active local model configuration."""
        return AIModelConfig(
            model_name=getattr(settings, "OLLAMA_MODEL", "llama3"),
            temperature=float(getattr(settings, "OLLAMA_TEMPERATURE", 0.2)),
            token_limit=int(getattr(settings, "OLLAMA_NUM_PREDICT", 512)),
            timeout_seconds=int(getattr(settings, "OLLAMA_TIMEOUT_SECONDS", 30)),
            endpoint=getattr(settings, "OLLAMA_HOST", "http://localhost:11434"),
        )
