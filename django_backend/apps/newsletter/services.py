"""Service layer for Django-owned newsletter workflows."""

from django.utils import timezone

from .models import NewsletterSubscriber


class NewsletterService:
    """Own newsletter subscription reads and writes in Django."""

    def list_subscribers(self):
        """Return Django-owned newsletter subscribers."""
        return NewsletterSubscriber.objects.all()

    def subscribe(self, email, source="website"):
        """Create or reactivate a newsletter subscriber."""
        subscriber, created = NewsletterSubscriber.objects.get_or_create(
            email=email,
            defaults={
                "status": "subscribed",
                "source": source or "website",
            },
        )
        if not created and subscriber.status != "subscribed":
            subscriber.status = "subscribed"
            subscriber.source = source or subscriber.source or "website"
            subscriber.unsubscribed_at = None
            subscriber.subscribed_at = timezone.now()
            subscriber.save(update_fields=["status", "source", "unsubscribed_at", "subscribed_at"])
        return subscriber, created
