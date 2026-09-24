"""Application configuration for the local AI agent system."""

from django.apps import AppConfig


class AiAgentConfig(AppConfig):
    """Register the AI agent app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai_agent"

