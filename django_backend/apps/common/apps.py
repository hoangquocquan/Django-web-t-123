"""Common app configuration."""

from django.apps import AppConfig


class CommonConfig(AppConfig):
    """Register the common infrastructure app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"
