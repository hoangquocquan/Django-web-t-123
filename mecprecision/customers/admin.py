"""Cấu hình Django Admin cho module Customers."""

from django.contrib import admin

from .models import ContactRequest, Customer, CustomerNote, NewsletterSubscriber


class CustomerNoteInline(admin.TabularInline):
    """Hiển thị ghi chú ngay trong màn hình chi tiết khách hàng."""

    model = CustomerNote
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Màn hình quản trị khách hàng trong Django Admin."""

    list_display = ("id", "company_name", "contact_name", "email", "phone", "country", "created_at")
    search_fields = ("company_name", "contact_name", "email", "phone", "country")
    list_filter = ("country",)
    inlines = [CustomerNoteInline]


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    """Màn hình quản trị liên hệ khách gửi từ website."""

    list_display = ("id", "name", "company", "email", "phone", "status", "is_read", "created_at")
    search_fields = ("name", "company", "email", "phone", "contact", "interested_product", "message")
    list_filter = ("status", "is_read", "country")


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    """Màn hình quản trị email nhận newsletter."""

    list_display = ("id", "email", "status", "subscribed_at", "unsubscribed_at")
    search_fields = ("email",)
    list_filter = ("status",)
