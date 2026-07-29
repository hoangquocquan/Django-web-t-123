"""Prompt preparation helpers for local AI requests."""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ValidationError


@dataclass(frozen=True)
class PreparedPrompt:
    """Safe prompt payload passed to the Ollama client."""

    system_prompt: str
    user_message: str

    @property
    def combined(self):
        """Return the final prompt sent to the local model."""
        return f"{self.system_prompt}\n\nUser question:\n{self.user_message}"


class PromptManager:
    """Validate and prepare messages without storing sensitive content."""

    system_prompt = (
        "You are the local AI assistant for MecPrecision VIETNAM. "
        "Answer clearly, avoid exposing secrets, and ask for clarification "
        "when the request is outside available context."
    )

    def __init__(self, max_length=None):
        """Allow tests or settings to control the maximum message size."""
        self.max_length = max_length or getattr(settings, "AI_CHAT_MAX_MESSAGE_LENGTH", 2000)

    def prepare_chat_prompt(self, message):
        """Normalize one chat message and return a prepared prompt."""
        normalized = str(message or "").strip()
        if not normalized:
            raise ValidationError("Message is required.")
        if len(normalized) > self.max_length:
            raise ValidationError(f"Message must be {self.max_length} characters or fewer.")
        return PreparedPrompt(system_prompt=self.system_prompt, user_message=normalized)

