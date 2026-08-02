"""Remove old authentication token metadata after its retention period."""

from django.core.management.base import BaseCommand

from apps.foundation.services import FoundationAuthService


class Command(BaseCommand):
    """Expose bounded token cleanup as an operator-controlled command."""

    help = "Delete expired or revoked foundation token metadata after retention."

    def add_arguments(self, parser):
        """Accept a positive retention period in days."""
        parser.add_argument("--retention-days", type=int, default=30)

    def handle(self, *args, **options):
        """Run cleanup and report only a row count, never token values."""
        retention_days = options["retention_days"]
        if retention_days < 1:
            raise ValueError("retention-days must be positive")
        count = FoundationAuthService().cleanup_tokens(retention_days=retention_days)
        self.stdout.write(self.style.SUCCESS(f"Removed {count} stale token rows."))
