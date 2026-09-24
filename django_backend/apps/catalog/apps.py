"""Catalog app configuration."""

from django.apps import AppConfig


class CatalogConfig(AppConfig):
    """Register the catalog read-only ORM app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.catalog"
