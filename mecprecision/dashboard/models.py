"""Django models cho module Dashboard."""

from django.db import models
from django.utils import timezone


class PageVisit(models.Model):
    """Một lượt truy cập trang public, dùng để vẽ biểu đồ dashboard."""

    path = models.CharField(max_length=500)
    remote_addr = models.CharField(max_length=120, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    visited_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "page_visits"
        ordering = ["-id"]

    def __str__(self):
        return self.path
