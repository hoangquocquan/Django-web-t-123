"""Service layer cho Common/System."""

import json

from django.db import connection
from django.utils import timezone

from .models import CmsBanner, CmsMenuItem, CmsPage, EnterpriseEvent, JobQueue, Notification


def get_published_pages():
    """Lấy các trang động đã published."""
    return CmsPage.objects.filter(status="published").order_by("sort_order", "id")


def get_menu_items(location="header"):
    """Lấy menu item theo vị trí header/footer/sidebar."""
    return CmsMenuItem.objects.filter(location=location, status="published").order_by("sort_order", "id")


def get_active_banners(placement="home_slider"):
    """Lấy banner đang published theo placement."""
    now = timezone.now()
    return CmsBanner.objects.filter(placement=placement, status="published").filter(starts_at__isnull=True) | CmsBanner.objects.filter(
        placement=placement, status="published", starts_at__lte=now
    )


def publish_event(event_name, entity_type="", entity_id="", payload=None):
    """Tạo event nghiệp vụ để audit luồng hệ thống."""
    return EnterpriseEvent.objects.create(event_name=event_name, entity_type=entity_type, entity_id=str(entity_id or ""), payload=json.dumps(payload or {}, ensure_ascii=False))


def enqueue_job(job_type, payload=None):
    """Đưa một job vào queue xử lý nền."""
    return JobQueue.objects.create(job_type=job_type, payload=json.dumps(payload or {}, ensure_ascii=False))


def create_notification(title, message, level="info", recipient_type="admin", recipient_id=None):
    """Tạo thông báo nội bộ trong CMS."""
    return Notification.objects.create(title=title, message=message, level=level, recipient_type=recipient_type, recipient_id=recipient_id)


def health_check():
    """Kiểm tra nhanh hệ thống Django/database."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        database_ok = cursor.fetchone()[0] == 1
    return {"status": "ok" if database_ok else "error", "database": database_ok, "checked_at": timezone.now()}
