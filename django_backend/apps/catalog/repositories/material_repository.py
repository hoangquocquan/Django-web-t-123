"""Read-only repository adapter for catalog materials."""

from apps.catalog.models import Material
from apps.catalog.repositories.base import LegacyCatalogRepository


class MaterialRepository(LegacyCatalogRepository):
    """Access legacy materials through the Django ORM read-only mapping."""

    model = Material

    def list_materials(self):
        """Return all manufacturing materials from the legacy database."""
        return self.queryset().all()
