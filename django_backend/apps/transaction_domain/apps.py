"""Application configuration for Django-owned transaction domain."""

from django.apps import AppConfig


class TransactionDomainConfig(AppConfig):
    """Register the transaction domain app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.transaction_domain"
