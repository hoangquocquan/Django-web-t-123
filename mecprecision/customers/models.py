"""Django models cho module Customers.

Các model trong file này đang map vào những bảng SQLite đã có sẵn của project cũ.
`managed = False` nghĩa là Django chỉ dùng model để đọc/ghi dữ liệu, chưa tự quản lý
việc tạo bảng bằng migration ở giai đoạn này.
"""

from django.db import models
from django.utils import timezone


class Customer(models.Model):
    """Hồ sơ khách hàng hoặc công ty từng gửi liên hệ/yêu cầu báo giá."""

    company_name = models.CharField(max_length=255, blank=True, null=True)
    contact_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=80, blank=True, null=True)
    country = models.CharField(max_length=120, default="Vietnam")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "customers"
        ordering = ["-id"]

    def __str__(self):
        return self.company_name or self.contact_name


class ContactRequest(models.Model):
    """Form liên hệ khách gửi từ website public."""

    STATUS_NEW = "new"
    STATUS_PROCESSING = "processing"
    STATUS_DONE = "done"
    STATUS_CHOICES = [
        (STATUS_NEW, "Mới"),
        (STATUS_PROCESSING, "Đang xử lý"),
        (STATUS_DONE, "Đã xử lý"),
    ]

    name = models.CharField(max_length=255)
    contact = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=80, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=120, blank=True, null=True)
    interested_product = models.CharField(max_length=255, blank=True, null=True)
    attachment_url = models.TextField(blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_NEW)
    is_read = models.BooleanField(default=False)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "contact_requests"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.name} - {self.contact}"


class CustomerNote(models.Model):
    """Ghi chú chăm sóc khách hàng, ví dụ: đã gọi, đang chờ phản hồi."""

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="notes")
    note = models.TextField()
    created_by = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "customer_notes"
        ordering = ["-id"]

    def __str__(self):
        return self.note[:80]


class NewsletterSubscriber(models.Model):
    """Email đăng ký nhận bản tin."""

    STATUS_SUBSCRIBED = "subscribed"
    STATUS_UNSUBSCRIBED = "unsubscribed"
    STATUS_CHOICES = [
        (STATUS_SUBSCRIBED, "Đang nhận tin"),
        (STATUS_UNSUBSCRIBED, "Đã hủy"),
    ]

    email = models.EmailField(max_length=255, unique=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_SUBSCRIBED)
    subscribed_at = models.DateTimeField(default=timezone.now)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "newsletter_subscribers"
        ordering = ["-id"]

    def __str__(self):
        return self.email
