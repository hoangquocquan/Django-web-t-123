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


class SalesLead(models.Model):
    """Django-owned sales lead for the professional sales pipeline."""

    STATUS_CHOICES = [
        ("new", "New Lead"),
        ("contacted", "Contacted"),
        ("meeting", "Meeting"),
        ("quotation", "Quotation"),
        ("negotiation", "Negotiation"),
        ("won", "Won"),
        ("lost", "Lost"),
    ]

    lead_source = models.CharField(max_length=120, blank=True)
    company = models.CharField(max_length=220)
    contact_person = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=80, blank=True)
    industry = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="new")
    priority = models.CharField(max_length=40, default="medium")
    owner = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.SET_NULL,
        related_name="sales_leads",
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sales_platform_leads"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status"], name="sales_lead_status_idx"),
            models.Index(fields=["priority"], name="sales_lead_priority_idx"),
        ]

    def __str__(self):
        """Return a compact lead label."""
        return f"{self.company} - {self.status}"


class SalesOpportunity(models.Model):
    """Django-owned sales opportunity tied to a customer or lead."""

    STATUS_CHOICES = [
        ("open", "Open"),
        ("proposal", "Proposal"),
        ("negotiation", "Negotiation"),
        ("won", "Won"),
        ("lost", "Lost"),
    ]

    lead = models.ForeignKey(SalesLead, on_delete=models.SET_NULL, related_name="opportunities", blank=True, null=True)
    customer = models.ForeignKey(
        "business_core.BusinessCustomer",
        on_delete=models.SET_NULL,
        related_name="sales_opportunities",
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=220)
    value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    probability = models.PositiveIntegerField(default=10)
    expected_close_date = models.CharField(max_length=40, blank=True)
    sales_owner = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.SET_NULL,
        related_name="sales_opportunities",
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="open")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sales_platform_opportunities"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status"], name="sales_opp_status_idx"),
            models.Index(fields=["expected_close_date"], name="sales_opp_close_idx"),
        ]

    def __str__(self):
        """Return opportunity title."""
        return self.title


class SalesQuotation(models.Model):
    """Django-owned professional quotation header."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("review", "Review"),
        ("approved", "Approved"),
        ("sent", "Sent"),
        ("accepted", "Accepted"),
        ("lost", "Lost"),
    ]

    opportunity = models.ForeignKey(
        SalesOpportunity,
        on_delete=models.SET_NULL,
        related_name="quotations",
        blank=True,
        null=True,
    )
    customer = models.ForeignKey(
        "business_core.BusinessCustomer",
        on_delete=models.SET_NULL,
        related_name="sales_quotations",
        blank=True,
        null=True,
    )
    quotation_number = models.CharField(max_length=80, unique=True)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="draft")
    approval_status = models.CharField(max_length=40, default="pending")
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_by = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.SET_NULL,
        related_name="sales_quotations",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sales_platform_quotations"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status"], name="sales_quote_status_idx"),
            models.Index(fields=["approval_status"], name="sales_quote_approval_idx"),
        ]

    def __str__(self):
        """Return quotation number."""
        return self.quotation_number


class SalesQuotationLine(models.Model):
    """Django-owned line item inside a professional quotation."""

    quotation = models.ForeignKey(SalesQuotation, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(
        "business_core.BusinessProduct",
        on_delete=models.SET_NULL,
        related_name="sales_quote_lines",
        blank=True,
        null=True,
    )
    description = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = "sales_platform_quotation_lines"
        ordering = ["id"]

    def __str__(self):
        """Return a compact line label."""
        return self.description or f"Quotation line #{self.id}"


class SalesFollowUp(models.Model):
    """Follow-up task or reminder for a lead, opportunity, or customer."""

    lead = models.ForeignKey(SalesLead, on_delete=models.CASCADE, related_name="follow_ups", blank=True, null=True)
    opportunity = models.ForeignKey(
        SalesOpportunity,
        on_delete=models.CASCADE,
        related_name="follow_ups",
        blank=True,
        null=True,
    )
    customer = models.ForeignKey(
        "business_core.BusinessCustomer",
        on_delete=models.SET_NULL,
        related_name="sales_follow_ups",
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=220)
    due_date = models.CharField(max_length=40, blank=True)
    status = models.CharField(max_length=40, default="open")
    owner = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.SET_NULL,
        related_name="sales_follow_ups",
        blank=True,
        null=True,
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sales_platform_follow_ups"
        ordering = ["status", "due_date", "-id"]


class SalesActivity(models.Model):
    """Timeline activity for sales communication and notes."""

    lead = models.ForeignKey(SalesLead, on_delete=models.CASCADE, related_name="activities", blank=True, null=True)
    opportunity = models.ForeignKey(
        SalesOpportunity,
        on_delete=models.CASCADE,
        related_name="activities",
        blank=True,
        null=True,
    )
    customer = models.ForeignKey(
        "business_core.BusinessCustomer",
        on_delete=models.SET_NULL,
        related_name="sales_activities",
        blank=True,
        null=True,
    )
    activity_type = models.CharField(max_length=80, default="note")
    subject = models.CharField(max_length=220)
    content = models.TextField(blank=True)
    created_by = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sales_platform_activities"
        ordering = ["-created_at", "-id"]
