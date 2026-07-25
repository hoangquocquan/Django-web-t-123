"""Sales app configuration."""

from django.apps import AppConfig


class SalesConfig(AppConfig):
    """Register the sales read-only ORM app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.sales"
