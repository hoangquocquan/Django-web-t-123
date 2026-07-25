"""Django models cho các bảng dùng chung của CMS/System."""

from django.db import models
from django.utils import timezone


class CmsPage(models.Model):
    """Trang động trong CMS, ví dụ About, Contact, Privacy, Terms."""

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField(blank=True, null=True)
    seo_title = models.CharField(max_length=255, blank=True, null=True)
    seo_description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=30, default="draft")
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "cms_pages"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class CmsMenuItem(models.Model):
    """Menu Builder: header, footer, sidebar và menu lồng nhau."""

    location = models.CharField(max_length=80, default="header")
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True, db_column="parent_id")
    label = models.CharField(max_length=255)
    url = models.TextField()
    sort_order = models.IntegerField(default=0)
    status = models.CharField(max_length=30, default="published")

    class Meta:
        managed = False
        db_table = "cms_menu_items"
        ordering = ["location", "sort_order", "id"]

    def __str__(self):
        return self.label


class CmsBanner(models.Model):
    """Banner cho slider trang chủ, popup hoặc advertisement."""

    title = models.CharField(max_length=255)
    placement = models.CharField(max_length=80, default="home_slider")
    image_url = models.TextField(blank=True, null=True)
    link_url = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    status = models.CharField(max_length=30, default="draft")
    starts_at = models.DateTimeField(blank=True, null=True)
    ends_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "cms_banners"
        ordering = ["placement", "sort_order", "id"]

    def __str__(self):
        return self.title


class EnterpriseEvent(models.Model):
    """Event nghiệp vụ để truy vết luồng hệ thống."""

    event_name = models.CharField(max_length=120)
    entity_type = models.CharField(max_length=120, blank=True, null=True)
    entity_id = models.CharField(max_length=120, blank=True, null=True)
    payload = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=40, default="published")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "enterprise_events"
        ordering = ["-id"]


class JobQueue(models.Model):
    """Queue xử lý nền: email, notification, backup."""

    job_type = models.CharField(max_length=120)
    payload = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=40, default="pending")
    attempts = models.IntegerField(default=0)
    available_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    last_error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "job_queue"
        ordering = ["-id"]


class Notification(models.Model):
    """Thông báo nội bộ trong CMS."""

    recipient_type = models.CharField(max_length=80, default="admin")
    recipient_id = models.IntegerField(blank=True, null=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    level = models.CharField(max_length=40, default="info")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "notifications"
        ordering = ["-id"]
