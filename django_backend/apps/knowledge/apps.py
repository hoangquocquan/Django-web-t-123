"""Application configuration for the knowledge engine."""

from django.apps import AppConfig


class KnowledgeConfig(AppConfig):
    """Register the RAG knowledge app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.knowledge"

