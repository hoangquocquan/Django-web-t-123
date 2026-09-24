"""Read-only repository adapter for CMS menu items."""

from django.db.models import Prefetch

from apps.cms.models import CmsMenuItem
from apps.cms.repositories.base import LegacyCmsRepository


class CmsMenuRepository(LegacyCmsRepository):
    """Read menu items from the legacy database."""

    model = CmsMenuItem

    def list_menu_items(self):
        """Return all menu items with parent loaded."""
        return self.queryset().select_related("parent").all()

    def list_menu_by_location(self, location):
        """Return menu items for one location such as header or footer."""
        return self.list_menu_items().filter(location=location)

    def list_root_menu_items(self, location=None):
        """Return root menu items and preload children for nested menu rendering."""
        queryset = self.queryset().filter(parent_id__isnull=True)
        if location:
            queryset = queryset.filter(location=location)
        return queryset.prefetch_related(
            Prefetch("children", queryset=self.queryset().order_by("sort_order", "id"))
        )

    def get_menu_item(self, item_id):
        """Return one menu item by legacy ID."""
        return self.list_menu_items().get(id=item_id)
