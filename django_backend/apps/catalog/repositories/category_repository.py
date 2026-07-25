"""Read-only repository adapter for catalog categories."""

from apps.catalog.models import Category
from apps.catalog.repositories.base import LegacyCatalogRepository


class CategoryRepository(LegacyCatalogRepository):
    """Access legacy categories through the Django ORM read-only mapping."""

    model = Category

    def list_categories(self):
        """Return all categories from the legacy database."""
        return self.queryset().all()

    def get_category(self, category_id):
        """Return one category by legacy ID."""
        return self.queryset().get(id=category_id)
