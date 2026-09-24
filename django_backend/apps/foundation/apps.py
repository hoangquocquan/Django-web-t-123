"""Application config for Django-owned foundation services."""

from django.apps import AppConfig


class FoundationConfig(AppConfig):
    """Register the foundation ownership app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.foundation"
