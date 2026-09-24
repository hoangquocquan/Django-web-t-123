"""Application config for the Django-owned newsletter domain."""

from django.apps import AppConfig


class NewsletterConfig(AppConfig):
    """Register the newsletter ownership app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.newsletter"
