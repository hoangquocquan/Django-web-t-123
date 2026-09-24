"""Application configuration for Django-owned business core."""

from django.apps import AppConfig


class BusinessCoreConfig(AppConfig):
    """Register the business core app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.business_core"
