"""Read-only unmanaged ORM models for legacy CRM tables."""

from django.db import models

from apps.common.models import LegacyReadOnlyModel


class Customer(LegacyReadOnlyModel):
    """Khách hàng hoặc công ty đã gửi thông tin cho MecPrecision."""

    id = models.IntegerField(primary_key=True)
    company_name = models.TextField(blank=True, null=True)
    contact_name = models.TextField()
    email = models.TextField(blank=True, null=True)
    phone = models.TextField(blank=True, null=True)
    country = models.TextField(default="Vietnam", blank=True, null=True)
    created_at = models.TextField()

    class Meta:
        managed = False
        db_table = "customers"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.company_name or self.contact_name


class CustomerNote(LegacyReadOnlyModel):
    """Ghi chú chăm sóc khách hàng trong CRM legacy."""

    id = models.IntegerField(primary_key=True)
    customer = models.ForeignKey(
        Customer,
        db_column="customer_id",
        on_delete=models.CASCADE,
        related_name="notes",
    )
    note = models.TextField()
    created_by = models.TextField(blank=True, null=True)
    created_at = models.TextField()

    class Meta:
        managed = False
        db_table = "customer_notes"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.note


class ContactRequest(LegacyReadOnlyModel):
    """Form liên hệ public được lưu trong database legacy."""

    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    contact = models.TextField()
    message = models.TextField(blank=True, null=True)
    status = models.TextField(default="new")
    created_at = models.TextField()
    is_read = models.BooleanField(default=False)
    note = models.TextField(blank=True, null=True)
    company = models.TextField(blank=True, null=True)
    phone = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    interested_product = models.TextField(blank=True, null=True)
    attachment_url = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "contact_requests"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.name} - {self.status}"
