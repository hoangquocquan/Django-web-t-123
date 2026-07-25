"""Read-only unmanaged ORM models for legacy CMS tables."""

from django.db import models

from apps.common.models import LegacyReadOnlyModel


class CmsPage(LegacyReadOnlyModel):
    """Dynamic CMS page such as About, Contact or Terms."""

    id = models.IntegerField(primary_key=True)
    title = models.TextField()
    slug = models.TextField(unique=True)
    content = models.TextField(blank=True, null=True)
    seo_title = models.TextField(blank=True, null=True)
    seo_description = models.TextField(blank=True, null=True)
    status = models.TextField(default="draft")
    sort_order = models.IntegerField(default=0)
    created_at = models.TextField()
    updated_at = models.TextField()

    class Meta:
        managed = False
        db_table = "cms_pages"
        ordering = ["sort_order", "-id"]

    def __str__(self):
        return self.title


class CmsMenuItem(LegacyReadOnlyModel):
    """Nested CMS menu item for header, footer or sidebar navigation."""

    id = models.IntegerField(primary_key=True)
    location = models.TextField(default="header")
    parent = models.ForeignKey(
        "self",
        db_column="parent_id",
        on_delete=models.SET_NULL,
        related_name="children",
        blank=True,
        null=True,
    )
    label = models.TextField()
    url = models.TextField()
    sort_order = models.IntegerField(default=0)
    status = models.TextField(default="published")

    class Meta:
        managed = False
        db_table = "cms_menu_items"
        ordering = ["location", "parent_id", "sort_order", "id"]

    def __str__(self):
        return self.label


class CmsBanner(LegacyReadOnlyModel):
    """CMS banner for home slider, popup or advertisement placement."""

    id = models.IntegerField(primary_key=True)
    title = models.TextField()
    placement = models.TextField(default="home_slider")
    image_url = models.TextField(blank=True, null=True)
    link_url = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    status = models.TextField(default="draft")
    starts_at = models.TextField(blank=True, null=True)
    ends_at = models.TextField(blank=True, null=True)
    created_at = models.TextField()

    class Meta:
        managed = False
        db_table = "cms_banners"
        ordering = ["sort_order", "-id"]

    def __str__(self):
        return self.title


class NewsletterSubscriber(LegacyReadOnlyModel):
    """Newsletter subscriber record managed by legacy CMS."""

    id = models.IntegerField(primary_key=True)
    email = models.TextField(unique=True)
    status = models.TextField(default="subscribed")
    subscribed_at = models.TextField()
    unsubscribed_at = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "newsletter_subscribers"
        ordering = ["-id"]

    def __str__(self):
        return self.email
