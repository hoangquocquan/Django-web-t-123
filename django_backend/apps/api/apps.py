"""Django app config for the central API routing layer."""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Register the API layer without owning database models."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.api"
