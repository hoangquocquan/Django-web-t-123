"""Core app configuration."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for the core migration app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
