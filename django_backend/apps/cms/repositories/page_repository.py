"""Read-only repository adapter for CMS pages."""

from apps.cms.models import CmsPage
from apps.cms.repositories.base import LegacyCmsRepository


class CmsPageRepository(LegacyCmsRepository):
    """Read CMS pages from the legacy database."""

    model = CmsPage

    def list_pages(self):
        """Return all CMS pages."""
        return self.queryset().all()

    def list_published_pages(self):
        """Return published CMS pages for public navigation/content."""
        return self.queryset().filter(status="published")

    def get_page(self, page_id):
        """Return one CMS page by legacy ID."""
        return self.queryset().get(id=page_id)

    def get_published_page_by_slug(self, slug):
        """Return one published page by slug."""
        return self.queryset().get(slug=slug, status="published")
