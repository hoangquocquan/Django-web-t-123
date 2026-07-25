"""Read-only CMS service layer."""

from apps.cms.repositories.banner_repository import CmsBannerRepository
from apps.cms.repositories.menu_repository import CmsMenuRepository
from apps.cms.repositories.newsletter_repository import NewsletterRepository
from apps.cms.repositories.page_repository import CmsPageRepository


class CmsService:
    """Service for read-only CMS content workflows."""

    def __init__(
        self,
        page_repository=None,
        menu_repository=None,
        banner_repository=None,
        newsletter_repository=None,
    ):
        """Allow tests to pass repository doubles without touching the ORM."""
        self.page_repository = page_repository or CmsPageRepository()
        self.menu_repository = menu_repository or CmsMenuRepository()
        self.banner_repository = banner_repository or CmsBannerRepository()
        self.newsletter_repository = newsletter_repository or NewsletterRepository()

    def list_public_pages(self):
        """Return published pages."""
        return self.page_repository.list_published_pages()

    def list_public_news(self):
        """Return CMS-backed news replacement records."""
        return self.page_repository.list_published_pages()

    def get_public_page(self, slug):
        """Return one published page by slug."""
        return self.page_repository.get_published_page_by_slug(slug)

    def list_navigation(self, location):
        """Return root menu items and children for a navigation location."""
        return self.menu_repository.list_root_menu_items(location=location)

    def list_active_banners(self, placement):
        """Return active banners for a placement."""
        return self.banner_repository.list_active_banners(placement)

    def list_newsletter_subscribers(self):
        """Return newsletter subscribers for future export/read views."""
        return self.newsletter_repository.list_subscribers()
