"""Read-only repository adapter for manufacturing capabilities."""

from apps.catalog.models import Capability
from apps.catalog.repositories.base import LegacyCatalogRepository


class CapabilityRepository(LegacyCatalogRepository):
    """Read legacy capability records through the repository boundary."""

    model = Capability

    def list_capabilities(self):
        """Return all manufacturing capabilities."""
        return self.queryset().all()
