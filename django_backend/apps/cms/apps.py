"""CMS app configuration."""

from django.apps import AppConfig


class CmsConfig(AppConfig):
    """Register the CMS read-only ORM app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cms"
