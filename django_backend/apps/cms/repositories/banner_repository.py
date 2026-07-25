"""Read-only repository adapter for CMS banners."""

from apps.cms.models import CmsBanner
from apps.cms.repositories.base import LegacyCmsRepository


class CmsBannerRepository(LegacyCmsRepository):
    """Read CMS banners from the legacy database."""

    model = CmsBanner

    def list_banners(self):
        """Return all banners."""
        return self.queryset().all()

    def list_active_banners(self, placement):
        """Return published banners for one placement."""
        return self.queryset().filter(placement=placement, status="published")

    def get_banner(self, banner_id):
        """Return one banner by legacy ID."""
        return self.queryset().get(id=banner_id)
