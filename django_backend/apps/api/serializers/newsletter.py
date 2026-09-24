"""Serializers for Django-owned newsletter APIs."""

from rest_framework import serializers


class NewsletterSubscribeSerializer(serializers.Serializer):
    """Validate newsletter subscription requests."""

    email = serializers.EmailField()
    source = serializers.CharField(required=False, allow_blank=True, max_length=80)


def newsletter_subscriber_to_dict(subscriber):
    """Convert a Django-owned newsletter subscriber to API JSON."""
    return {
        "id": subscriber.id,
        "email": subscriber.email,
        "status": subscriber.status,
        "source": subscriber.source,
        "subscribed_at": subscriber.subscribed_at.isoformat() if subscriber.subscribed_at else None,
        "unsubscribed_at": subscriber.unsubscribed_at.isoformat() if subscriber.unsubscribed_at else None,
    }
