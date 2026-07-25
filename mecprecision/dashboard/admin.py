"""Cấu hình Django Admin cho Dashboard."""

from django.contrib import admin

from .models import PageVisit


@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    """Màn hình xem lượt truy cập public site."""

    list_display = ("id", "path", "remote_addr", "visited_at")
    search_fields = ("path", "remote_addr", "user_agent")
    list_filter = ("visited_at",)
