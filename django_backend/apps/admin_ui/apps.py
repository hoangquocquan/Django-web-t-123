"""Django app configuration for the migrated admin UI."""

from django.apps import AppConfig


class AdminUiConfig(AppConfig):
    """Register the browser-facing admin UI app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.admin_ui"
    verbose_name = "MEC Admin UI"
