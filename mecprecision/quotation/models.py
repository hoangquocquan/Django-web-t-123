"""Django models cho module Quotation.

Module này map các bảng báo giá cũ:
- `quote_requests`: thông tin yêu cầu báo giá tổng.
- `quote_request_items`: từng dòng chi tiết trong báo giá.
- `quote_files`: file bản vẽ/tài liệu khách gửi kèm.
"""

from django.db import models
from django.utils import timezone

from customers.models import Customer
from products.models import Material, Product


class QuoteRequest(models.Model):
    """Yêu cầu báo giá tổng, thuộc về một khách hàng."""

    STATUS_NEW = "new"
    STATUS_ASSIGNED = "assigned"
    STATUS_PROCESSING = "processing"
    STATUS_QUOTED = "quoted"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_NEW, "Yêu cầu mới"),
        (STATUS_ASSIGNED, "Đã phân công"),
        (STATUS_PROCESSING, "Đang xử lý"),
        (STATUS_QUOTED, "Đã báo giá"),
        (STATUS_COMPLETED, "Hoàn thành"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, db_column="customer_id", related_name="quotes")
    project_name = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_NEW)
    assigned_to = models.IntegerField(blank=True, null=True)
    internal_note = models.TextField(blank=True, null=True)
    quoted_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "quote_requests"
        ordering = ["-id"]

    def __str__(self):
        return self.project_name or f"Quote #{self.id}"


class QuoteRequestItem(models.Model):
    """Một dòng chi tiết trong yêu cầu báo giá."""

    quote_request = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True)
    drawing_code = models.CharField(max_length=255, blank=True, null=True)
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, blank=True, null=True)
    quantity = models.IntegerField(default=1)
    tolerance = models.CharField(max_length=120, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "quote_request_items"
        ordering = ["id"]

    def __str__(self):
        return self.drawing_code or f"Item #{self.id}"


class QuoteFile(models.Model):
    """File khách gửi kèm báo giá, ví dụ PDF, STEP, DWG."""

    quote_request = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name="files")
    file_name = models.CharField(max_length=255)
    file_url = models.TextField()
    file_type = models.CharField(max_length=80, blank=True, null=True)
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "quote_files"
        ordering = ["id"]

    def __str__(self):
        return self.file_name
