"""Managed Django models for newsletter ownership."""

from django.db import models


class NewsletterSubscriber(models.Model):
    """Django-owned newsletter subscriber.

    The table name intentionally matches the legacy table name so future
    database ownership can keep compatibility with existing reporting and
    export expectations.
    """

    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    status = models.CharField(max_length=32, default="subscribed")
    source = models.CharField(max_length=80, default="website")
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "newsletter_subscribers"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["status"], name="newsletter_status_idx"),
        ]

    def __str__(self):
        """Return the subscriber email for admin/debug display."""
        return self.email
