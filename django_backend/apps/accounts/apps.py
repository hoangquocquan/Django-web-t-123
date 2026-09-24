"""Accounts app configuration."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Register the authentication read-only ORM app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
