"""CRM app configuration."""

from django.apps import AppConfig


class CrmConfig(AppConfig):
    """Register the CRM read-only ORM app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.crm"
