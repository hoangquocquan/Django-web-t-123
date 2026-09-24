"""Django app configuration for the public website."""

from django.apps import AppConfig


class WebsiteConfig(AppConfig):
    """Register the public website app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.website"
    verbose_name = "MEC Public Website"
