from django.apps import AppConfig


class CustomersConfig(AppConfig):
    """Cấu hình app customers."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "customers"
