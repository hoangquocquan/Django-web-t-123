"""AI model configuration for local Ollama inference."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from django.conf import settings


class AIModelConfigurationError(ValueError):
    """Raised when a model is not approved for its intended AI purpose."""


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

    PURPOSE_SETTINGS: ClassVar[dict[str, tuple[str, str]]] = {
        "generation": ("OLLAMA_GENERATION_MODELS", "OLLAMA_MODEL"),
        "embedding": ("OLLAMA_EMBEDDING_MODELS", "OLLAMA_EMBEDDING_MODEL"),
        "review": ("OLLAMA_REVIEW_MODELS", "OLLAMA_REVIEW_MODEL"),
    }

    @staticmethod
    def _model_family(model_name):
        """Normalize optional Ollama tags while keeping model identity explicit."""
        return str(model_name or "").strip().split(":", 1)[0]

    def allowed_models(self, purpose="generation"):
        """Return the server-owned model allowlist for one controlled purpose."""
        try:
            list_setting, selected_setting = self.PURPOSE_SETTINGS[purpose]
        except KeyError as exc:
            raise AIModelConfigurationError(
                f"Unknown AI model purpose: {purpose}."
            ) from exc
        selected = str(getattr(settings, selected_setting, "")).strip()
        configured = getattr(settings, list_setting, ())
        if isinstance(configured, str):
            configured = configured.split(",")
        allowed = tuple(
            dict.fromkeys(str(item).strip() for item in configured if str(item).strip())
        )
        return allowed or ((selected,) if selected else ())

    def validate_model(self, model_name, purpose="generation"):
        """Reject arbitrary client/model selection outside the server allowlist."""
        selected = str(model_name or "").strip()
        families = {self._model_family(item) for item in self.allowed_models(purpose)}
        if not selected or self._model_family(selected) not in families:
            raise AIModelConfigurationError(
                f"Model is not approved for {purpose}: {selected or '<empty>'}."
            )
        return selected

    def current(self, purpose="generation"):
        """Return the active local model configuration."""
        selected_setting = self.PURPOSE_SETTINGS[purpose][1]
        selected_model = getattr(settings, selected_setting, "llama3")
        return AIModelConfig(
            model_name=self.validate_model(selected_model, purpose),
            temperature=float(getattr(settings, "OLLAMA_TEMPERATURE", 0.2)),
            token_limit=int(getattr(settings, "OLLAMA_NUM_PREDICT", 512)),
            timeout_seconds=int(getattr(settings, "OLLAMA_TIMEOUT_SECONDS", 30)),
            endpoint=getattr(settings, "OLLAMA_HOST", "http://localhost:11434"),
        )
