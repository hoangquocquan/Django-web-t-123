"""Cấu hình Django Admin cho module Quotation."""

from django.contrib import admin

from .models import QuoteFile, QuoteRequest, QuoteRequestItem


class QuoteRequestItemInline(admin.TabularInline):
    """Hiển thị các dòng chi tiết ngay trong màn hình báo giá."""

    model = QuoteRequestItem
    extra = 0


class QuoteFileInline(admin.TabularInline):
    """Hiển thị file đính kèm ngay trong màn hình báo giá."""

    model = QuoteFile
    extra = 0


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    """Màn hình quản trị workflow báo giá."""

    list_display = ("id", "project_name", "customer", "status", "assigned_to", "created_at")
    search_fields = ("project_name", "message", "customer__company_name", "customer__contact_name")
    list_filter = ("status",)
    inlines = [QuoteRequestItemInline, QuoteFileInline]


@admin.register(QuoteRequestItem)
class QuoteRequestItemAdmin(admin.ModelAdmin):
    """Màn hình quản trị từng dòng chi tiết báo giá."""

    list_display = ("id", "quote_request", "drawing_code", "quantity", "tolerance")
    search_fields = ("drawing_code", "note", "quote_request__project_name")


@admin.register(QuoteFile)
class QuoteFileAdmin(admin.ModelAdmin):
    """Màn hình quản trị file đính kèm báo giá."""

    list_display = ("id", "quote_request", "file_name", "file_type", "uploaded_at")
    search_fields = ("file_name", "file_url", "file_type")
