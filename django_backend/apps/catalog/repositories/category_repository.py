"""Read-only repository adapter for catalog categories."""

from apps.catalog.models import Category


class CategoryRepository:
    """Access legacy categories through the Django ORM read-only mapping."""

    database_alias = "legacy"

    def list_categories(self):
        """Return all categories from the legacy database."""
        return Category.objects.using(self.database_alias).all()

    def get_category(self, category_id):
        """Return one category by legacy ID."""
        return Category.objects.using(self.database_alias).get(id=category_id)
