"""Read-only unmanaged ORM models for legacy quotation tables."""

from django.db import models

from apps.catalog.models import Material, Product
from apps.common.models import LegacyReadOnlyModel
from apps.crm.models import Customer


class QuoteRequest(LegacyReadOnlyModel):
    """Header record for a customer quotation request."""

    id = models.IntegerField(primary_key=True)
    customer = models.ForeignKey(
        Customer,
        db_column="customer_id",
        on_delete=models.DO_NOTHING,
        related_name="quote_requests",
    )
    project_name = models.TextField(blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    status = models.TextField(default="new")
    assigned_to = models.IntegerField(blank=True, null=True)
    internal_note = models.TextField(blank=True, null=True)
    quoted_at = models.TextField(blank=True, null=True)
    completed_at = models.TextField(blank=True, null=True)
    created_at = models.TextField()

    class Meta:
        managed = False
        db_table = "quote_requests"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.project_name or f"Quote #{self.id}"


class QuoteRequestItem(LegacyReadOnlyModel):
    """One line item inside a quotation request."""

    id = models.IntegerField(primary_key=True)
    quote_request = models.ForeignKey(
        QuoteRequest,
        db_column="quote_request_id",
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        db_column="product_id",
        on_delete=models.DO_NOTHING,
        related_name="quote_items",
        blank=True,
        null=True,
    )
    drawing_code = models.TextField(blank=True, null=True)
    material = models.ForeignKey(
        Material,
        db_column="material_id",
        on_delete=models.DO_NOTHING,
        related_name="quote_items",
        blank=True,
        null=True,
    )
    quantity = models.IntegerField(default=1)
    tolerance = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "quote_request_items"
        ordering = ["id"]

    def __str__(self):
        return self.drawing_code or f"Quote item #{self.id}"


class QuoteFile(LegacyReadOnlyModel):
    """Customer uploaded file attached to a quotation request."""

    id = models.IntegerField(primary_key=True)
    quote_request = models.ForeignKey(
        QuoteRequest,
        db_column="quote_request_id",
        on_delete=models.CASCADE,
        related_name="files",
    )
    file_name = models.TextField()
    file_url = models.TextField()
    file_type = models.TextField(blank=True, null=True)
    uploaded_at = models.TextField()

    class Meta:
        managed = False
        db_table = "quote_files"
        ordering = ["id"]

    def __str__(self):
        return self.file_name
