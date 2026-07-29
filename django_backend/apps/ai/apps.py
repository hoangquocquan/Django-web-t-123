"""Application configuration for the AI foundation layer."""

from django.apps import AppConfig


class AiConfig(AppConfig):
    """Register the local AI integration app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai"

