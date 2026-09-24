"""Read-only repository adapter for newsletter subscribers."""

from apps.cms.models import NewsletterSubscriber
from apps.cms.repositories.base import LegacyCmsRepository


class NewsletterRepository(LegacyCmsRepository):
    """Read newsletter subscribers from the legacy database."""

    model = NewsletterSubscriber

    def list_subscribers(self):
        """Return all newsletter subscribers."""
        return self.queryset().all()

    def list_subscribers_by_status(self, status):
        """Return subscribers filtered by subscription status."""
        return self.queryset().filter(status=status)

    def get_subscriber(self, subscriber_id):
        """Return one subscriber by legacy ID."""
        return self.queryset().get(id=subscriber_id)
