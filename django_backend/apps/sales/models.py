"""Legacy quotation projections and Django-owned sales-domain models."""

import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

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


QUOTATION_WORKFLOW_STATUS_CHOICES = [
    ("DRAFT", "Draft"),
    ("PENDING_APPROVAL", "Pending approval"),
    ("APPROVED", "Approved"),
    ("REJECTED", "Rejected"),
    ("SENT", "Sent"),
    ("ACCEPTED", "Accepted"),
    ("DECLINED", "Declined"),
    ("EXPIRED", "Expired"),
    ("SUPERSEDED", "Superseded"),
]
QUOTATION_CURRENCY_CHOICES = [("VND", "Vietnamese dong"), ("USD", "US dollar")]
QUOTATION_UNIT_CHOICES = [
    ("PCS", "Pieces"),
    ("KG", "Kilograms"),
    ("M", "Metres"),
    ("MM", "Millimetres"),
]
QUOTATION_APPROVAL_DECISION_CHOICES = [
    ("APPROVED", "Approved"),
    ("REJECTED", "Rejected"),
]
QUOTATION_CUSTOMER_DECISION_CHOICES = [
    ("ACCEPTED", "Accepted"),
    ("DECLINED", "Declined"),
]


class SalesQuotation(models.Model):
    """One canonical immutable quotation revision plus legacy compatibility."""

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
    data_contract = models.CharField(
        max_length=16,
        choices=[("LEGACY", "Legacy"), ("MVP_V1", "MVP V1")],
        default="LEGACY",
        db_index=True,
    )
    rfq = models.ForeignKey(
        "SalesRfq",
        on_delete=models.PROTECT,
        related_name="quotations",
        blank=True,
        null=True,
    )
    quotation_number = models.CharField(max_length=80, unique=True)
    version = models.PositiveIntegerField(default=1)
    revision = models.PositiveIntegerField(blank=True, null=True)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="draft")
    workflow_status = models.CharField(
        max_length=24,
        choices=QUOTATION_WORKFLOW_STATUS_CHOICES,
        blank=True,
        null=True,
        db_index=True,
    )
    approval_status = models.CharField(max_length=40, default="pending")
    currency = models.CharField(
        max_length=3,
        choices=QUOTATION_CURRENCY_CHOICES,
        blank=True,
        null=True,
    )
    valid_from = models.DateField(blank=True, null=True)
    valid_until = models.DateField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    discount_total = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    tax_amount = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    total = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    terms = models.TextField(blank=True)
    customer_snapshot = models.JSONField(default=dict, blank=True)
    rfq_snapshot = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    sent_to = models.CharField(max_length=254, blank=True)
    sent_evidence = models.TextField(blank=True)
    idempotency_key = models.CharField(max_length=64, blank=True, null=True)
    request_hash = models.CharField(max_length=64, blank=True)
    created_by = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.SET_NULL,
        related_name="sales_quotations",
        blank=True,
        null=True,
    )
    updated_by = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.PROTECT,
        related_name="updated_sales_quotations",
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
            models.Index(fields=["rfq", "revision"], name="sales_quote_rfq_rev_idx"),
            models.Index(fields=["workflow_status", "valid_until"], name="sales_quote_flow_valid_idx"),
            models.Index(fields=["created_by"], name="sales_quote_creator_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["rfq", "revision"],
                condition=models.Q(rfq__isnull=False, revision__isnull=False),
                name="uq_quote_rfq_revision",
            ),
            models.UniqueConstraint(
                fields=["rfq"],
                condition=models.Q(
                    data_contract="MVP_V1",
                    workflow_status__in=["APPROVED", "SENT", "ACCEPTED"],
                ),
                name="uq_quote_effective_rfq",
            ),
            models.UniqueConstraint(
                fields=["idempotency_key"],
                condition=models.Q(idempotency_key__isnull=False),
                name="uq_quote_idempotency_nonnull",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | models.Q(workflow_status__in=[choice[0] for choice in QUOTATION_WORKFLOW_STATUS_CHOICES])
                ),
                name="ck_quote_workflow_status",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | (
                        models.Q(rfq__isnull=False)
                        & models.Q(customer__isnull=False)
                        & models.Q(revision__isnull=False)
                        & models.Q(workflow_status__isnull=False)
                        & models.Q(currency__isnull=False)
                        & models.Q(valid_from__isnull=False)
                        & models.Q(valid_until__isnull=False)
                        & models.Q(created_by__isnull=False)
                        & models.Q(idempotency_key__isnull=False)
                        & ~models.Q(quotation_number="")
                        & ~models.Q(request_hash="")
                    )
                ),
                name="ck_quote_v1_required",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | models.Q(currency__in=[choice[0] for choice in QUOTATION_CURRENCY_CHOICES])
                ),
                name="ck_quote_currency",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | models.Q(valid_until__gte=models.F("valid_from"))
                ),
                name="ck_quote_validity",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | (
                        models.Q(subtotal__gte=0)
                        & models.Q(discount_total__gte=0)
                        & models.Q(tax_amount__gte=0)
                        & models.Q(total__gte=0)
                    )
                ),
                name="ck_quote_money_nonneg",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | models.Q(discount_total__lte=models.F("subtotal"))
                ),
                name="ck_quote_discount_bound",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | models.Q(
                        total=models.F("subtotal")
                        - models.F("discount_total")
                        + models.F("tax_amount")
                    )
                ),
                name="ck_quote_total_equation",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(idempotency_key__isnull=True, request_hash="")
                    | (models.Q(idempotency_key__isnull=False) & ~models.Q(request_hash=""))
                ),
                name="ck_quote_idempotency_pair",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(idempotency_key__isnull=True)
                    | models.Q(request_hash__regex=r"^[0-9a-fA-F]{64}$")
                ),
                name="ck_quote_request_hash",
            ),
        ]

    IMMUTABLE_REVISION_FIELDS = (
        "data_contract",
        "rfq_id",
        "customer_id",
        "quotation_number",
        "revision",
        "currency",
        "valid_from",
        "valid_until",
        "subtotal",
        "discount_total",
        "tax_amount",
        "total",
        "terms",
        "customer_snapshot",
        "rfq_snapshot",
        "idempotency_key",
        "request_hash",
        "created_by_id",
    )
    WORKFLOW_TRANSITIONS = {
        "DRAFT": {"PENDING_APPROVAL", "SUPERSEDED"},
        "PENDING_APPROVAL": {"APPROVED", "REJECTED"},
        "REJECTED": {"SUPERSEDED"},
        "APPROVED": {"SENT", "SUPERSEDED"},
        "SENT": {"ACCEPTED", "DECLINED", "EXPIRED", "SUPERSEDED"},
        "ACCEPTED": set(),
        "DECLINED": set(),
        "EXPIRED": set(),
        "SUPERSEDED": set(),
    }

    def save(self, *args, **kwargs):
        """Prevent in-place commercial edits after a V1 revision is submitted."""
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).values(
                "workflow_status", *self.IMMUTABLE_REVISION_FIELDS
            ).first()
            if (
                previous
                and previous["data_contract"] == "MVP_V1"
                and previous["workflow_status"] != "DRAFT"
            ):
                if any(
                    previous[field] != getattr(self, field)
                    for field in self.IMMUTABLE_REVISION_FIELDS
                ):
                    raise RuntimeError(
                        "Submitted SalesQuotation commercial snapshots are immutable."
                    )
            if (
                previous
                and previous["data_contract"] == "MVP_V1"
                and previous["workflow_status"] != self.workflow_status
                and self.workflow_status
                not in self.WORKFLOW_TRANSITIONS.get(previous["workflow_status"], set())
            ):
                raise RuntimeError("Invalid SalesQuotation workflow transition.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.data_contract == "MVP_V1" and self.workflow_status != "DRAFT":
            raise RuntimeError("Submitted SalesQuotation revisions cannot be deleted.")
        return super().delete(*args, **kwargs)

    def __str__(self):
        """Return quotation number."""
        return self.quotation_number


class SalesQuotationLineQuerySet(models.QuerySet):
    """Guard locked V1 commercial snapshots from bulk mutation."""

    def _contains_locked_rows(self):
        return self.filter(quotation__data_contract="MVP_V1").exclude(
            quotation__workflow_status="DRAFT"
        ).exists()

    def update(self, **kwargs):
        if self._contains_locked_rows():
            raise RuntimeError("Submitted quotation lines are immutable.")
        return super().update(**kwargs)

    def delete(self):
        if self._contains_locked_rows():
            raise RuntimeError("Submitted quotation lines are immutable.")
        return super().delete()


class SalesQuotationLine(models.Model):
    """Immutable commercial snapshot line for one quotation revision."""

    quotation = models.ForeignKey(SalesQuotation, on_delete=models.CASCADE, related_name="lines")
    data_contract = models.CharField(
        max_length=16,
        choices=[("LEGACY", "Legacy"), ("MVP_V1", "MVP V1")],
        default="LEGACY",
        db_index=True,
    )
    line_number = models.PositiveIntegerField(blank=True, null=True)
    source_rfq_line = models.ForeignKey(
        "SalesRfqLine",
        on_delete=models.PROTECT,
        related_name="quotation_lines",
        blank=True,
        null=True,
    )
    product = models.ForeignKey(
        "business_core.BusinessProduct",
        on_delete=models.SET_NULL,
        related_name="sales_quote_lines",
        blank=True,
        null=True,
    )
    description = models.TextField(blank=True)
    part_code_snapshot = models.CharField(max_length=32, blank=True)
    material_snapshot = models.CharField(max_length=240, blank=True)
    unit = models.CharField(max_length=8, choices=QUOTATION_UNIT_CHOICES, blank=True)
    quantity = models.DecimalField(max_digits=16, decimal_places=4, default=1)
    unit_price = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    discount = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    line_subtotal = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    line_total = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    objects = SalesQuotationLineQuerySet.as_manager()

    class Meta:
        db_table = "sales_platform_quotation_lines"
        ordering = ["quotation_id", "line_number", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["quotation", "line_number"],
                condition=models.Q(line_number__isnull=False),
                name="uq_quoteline_parent_number",
            ),
            models.CheckConstraint(
                condition=models.Q(line_number__isnull=True) | models.Q(line_number__gt=0),
                name="ck_quoteline_number_pos",
            ),
            models.CheckConstraint(
                condition=~models.Q(data_contract="MVP_V1") | models.Q(quantity__gt=0),
                name="ck_quoteline_quantity_pos",
            ),
            models.CheckConstraint(
                condition=~models.Q(data_contract="MVP_V1") | models.Q(unit_price__gt=0),
                name="ck_quoteline_price_pos",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | (
                        models.Q(discount__gte=0)
                        & models.Q(line_subtotal__gte=0)
                        & models.Q(line_total__gte=0)
                    )
                ),
                name="ck_quoteline_money_nonneg",
            ),
            models.CheckConstraint(
                condition=models.Q(unit="") | models.Q(
                    unit__in=[choice[0] for choice in QUOTATION_UNIT_CHOICES]
                ),
                name="ck_quoteline_unit",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | (
                        models.Q(line_number__isnull=False)
                        & models.Q(source_rfq_line__isnull=False)
                        & ~models.Q(description="")
                        & ~models.Q(part_code_snapshot="")
                        & ~models.Q(unit="")
                    )
                ),
                name="ck_quoteline_v1_required",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | models.Q(discount__lte=models.F("line_subtotal"))
                ),
                name="ck_quoteline_discount_bound",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | models.Q(
                        line_total=models.F("line_subtotal") - models.F("discount")
                    )
                ),
                name="ck_quoteline_total_equation",
            ),
        ]

    def clean(self):
        super().clean()
        if self.source_rfq_line_id and self.quotation.rfq_id:
            if self.source_rfq_line.rfq_id != self.quotation.rfq_id:
                raise ValidationError(
                    {"source_rfq_line": "The source line must belong to the same RFQ."}
                )

    def save(self, *args, **kwargs):
        quotation_state = SalesQuotation.objects.filter(pk=self.quotation_id).values_list(
            "data_contract", "workflow_status"
        ).first()
        if quotation_state and quotation_state[0] == "MVP_V1" and quotation_state[1] != "DRAFT":
            raise RuntimeError("Submitted quotation lines are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        quotation_state = SalesQuotation.objects.filter(pk=self.quotation_id).values_list(
            "data_contract", "workflow_status"
        ).first()
        if quotation_state and quotation_state[0] == "MVP_V1" and quotation_state[1] != "DRAFT":
            raise RuntimeError("Submitted quotation lines are immutable.")
        return super().delete(*args, **kwargs)

    def __str__(self):
        """Return a compact line label."""
        return self.description or f"Quotation line #{self.id}"


class AppendOnlyQuotationDecisionQuerySet(models.QuerySet):
    """Block mutation of quotation decision evidence."""

    def update(self, **kwargs):
        raise RuntimeError("Quotation decision records are append-only.")

    def delete(self):
        raise RuntimeError("Quotation decision records are append-only.")


class SalesQuotationApprovalDecision(models.Model):
    """Immutable Manager approval or rejection evidence."""

    quotation = models.ForeignKey(
        SalesQuotation,
        on_delete=models.PROTECT,
        related_name="approval_decisions",
    )
    reviewer = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.PROTECT,
        related_name="quotation_approval_decisions",
    )
    decision = models.CharField(max_length=16, choices=QUOTATION_APPROVAL_DECISION_CHOICES)
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    decided_at = models.DateTimeField(default=timezone.now)

    objects = AppendOnlyQuotationDecisionQuerySet.as_manager()

    class Meta:
        db_table = "sales_quotation_approval_decisions"
        ordering = ["quotation_id", "decided_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["quotation"], name="uq_quote_approval_decision"),
            models.CheckConstraint(
                condition=models.Q(
                    decision__in=[choice[0] for choice in QUOTATION_APPROVAL_DECISION_CHOICES]
                ),
                name="ck_quoteapproval_decision",
            ),
            models.CheckConstraint(
                condition=~models.Q(decision="REJECTED") | ~models.Q(reason=""),
                name="ck_quoteapproval_reason",
            ),
        ]

    def clean(self):
        super().clean()
        if self.quotation_id and self.reviewer_id == self.quotation.created_by_id:
            raise ValidationError({"reviewer": "Quotation creator cannot approve or reject it."})

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise RuntimeError("Quotation decision records are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Quotation decision records are append-only.")


class SalesQuotationCustomerDecision(models.Model):
    """Immutable customer acceptance or decline evidence."""

    quotation = models.ForeignKey(
        SalesQuotation,
        on_delete=models.PROTECT,
        related_name="customer_decisions",
    )
    recorded_by = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.PROTECT,
        related_name="recorded_customer_decisions",
    )
    decision = models.CharField(max_length=16, choices=QUOTATION_CUSTOMER_DECISION_CHOICES)
    contact_snapshot = models.CharField(max_length=254)
    evidence = models.TextField()
    reason = models.TextField(blank=True)
    decided_at = models.DateTimeField(default=timezone.now)

    objects = AppendOnlyQuotationDecisionQuerySet.as_manager()

    class Meta:
        db_table = "sales_quotation_customer_decisions"
        ordering = ["quotation_id", "decided_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["quotation"], name="uq_quote_customer_decision"),
            models.CheckConstraint(
                condition=models.Q(
                    decision__in=[choice[0] for choice in QUOTATION_CUSTOMER_DECISION_CHOICES]
                ),
                name="ck_quotecustomer_decision",
            ),
            models.CheckConstraint(
                condition=~models.Q(contact_snapshot="") & ~models.Q(evidence=""),
                name="ck_quotecustomer_required",
            ),
            models.CheckConstraint(
                condition=~models.Q(decision="DECLINED") | ~models.Q(reason=""),
                name="ck_quotecustomer_reason",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise RuntimeError("Quotation decision records are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Quotation decision records are append-only.")


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


DATA_CONTRACT_CHOICES = [("LEGACY", "Legacy"), ("MVP_V1", "MVP V1")]
RFQ_STATUS_CHOICES = [
    ("DRAFT", "Draft"),
    ("SUBMITTED", "Submitted"),
    ("UNDER_REVIEW", "Under review"),
    ("NEEDS_INFORMATION", "Needs information"),
    ("READY_TO_QUOTE", "Ready to quote"),
    ("QUOTED", "Quoted"),
    ("DECLINED", "Declined"),
    ("CLOSED", "Closed"),
]
RFQ_UNIT_CHOICES = [
    ("PCS", "Pieces"),
    ("KG", "Kilograms"),
    ("M", "Metres"),
    ("MM", "Millimetres"),
]
RFQ_DOCUMENT_MIME_CHOICES = [
    ("application/pdf", "PDF"),
    ("application/step", "STEP"),
    ("model/step", "STEP model"),
    ("application/dxf", "DXF"),
    ("image/vnd.dxf", "DXF image"),
    (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Excel workbook",
    ),
]
TECHNICAL_REVIEW_DECISION_CHOICES = [
    ("STARTED", "Started"),
    ("NEEDS_INFORMATION", "Needs information"),
    ("READY_TO_QUOTE", "Ready to quote"),
    ("DECLINED", "Declined"),
]


class SalesRfq(models.Model):
    """Django-owned request-for-quotation aggregate header."""

    data_contract = models.CharField(
        max_length=16,
        choices=DATA_CONTRACT_CHOICES,
        default="MVP_V1",
        db_index=True,
    )
    legacy_quote_request_id = models.IntegerField(blank=True, null=True)
    rfq_number = models.CharField(max_length=32)
    quotation_family_number = models.CharField(max_length=24, blank=True, null=True)
    idempotency_key = models.CharField(max_length=64, blank=True, null=True)
    request_hash = models.CharField(max_length=64, blank=True, null=True)
    customer = models.ForeignKey(
        "business_core.BusinessCustomer",
        on_delete=models.PROTECT,
        related_name="rfqs",
    )
    status = models.CharField(
        max_length=24,
        choices=RFQ_STATUS_CHOICES,
        default="DRAFT",
        db_index=True,
    )
    project_name = models.CharField(max_length=220, blank=True)
    notes = models.TextField(blank=True)
    quote_due_at = models.DateField()
    required_delivery_date = models.DateField()
    assigned_to = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.SET_NULL,
        related_name="assigned_rfqs",
        blank=True,
        null=True,
    )
    closure_reason = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.PROTECT,
        related_name="created_rfqs",
    )
    updated_by = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.PROTECT,
        related_name="updated_rfqs",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sales_rfqs"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status", "quote_due_at"], name="sales_rfq_status_due_idx"),
            models.Index(fields=["customer"], name="sales_rfq_customer_idx"),
            models.Index(fields=["assigned_to"], name="sales_rfq_assignee_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["rfq_number"], name="uq_rfq_number"),
            models.UniqueConstraint(
                fields=["quotation_family_number"],
                condition=models.Q(quotation_family_number__isnull=False),
                name="uq_rfq_quote_family_nonnull",
            ),
            models.UniqueConstraint(
                fields=["idempotency_key"],
                condition=models.Q(idempotency_key__isnull=False),
                name="uq_rfq_idempotency_nonnull",
            ),
            models.UniqueConstraint(
                fields=["legacy_quote_request_id"],
                condition=models.Q(legacy_quote_request_id__isnull=False),
                name="uq_rfq_legacy_quote_id",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | (
                        models.Q(idempotency_key__isnull=True, request_hash__isnull=True)
                        | models.Q(idempotency_key__isnull=False, request_hash__isnull=False)
                    )
                ),
                name="ck_rfq_idempotency_pair_v1",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=[choice[0] for choice in RFQ_STATUS_CHOICES]),
                name="ck_rfq_status",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | (~models.Q(rfq_number="") & models.Q(created_by__isnull=False))
                ),
                name="ck_rfq_v1_required",
            ),
            models.CheckConstraint(
                condition=models.Q(quote_due_at__lte=models.F("required_delivery_date")),
                name="ck_rfq_due_order",
            ),
            models.CheckConstraint(
                condition=(~models.Q(status="CLOSED") | ~models.Q(closure_reason="")),
                name="ck_rfq_close_reason",
            ),
        ]

    def __str__(self):
        return self.rfq_number


class SalesRfqLine(models.Model):
    """Requested part or free-text work item inside an RFQ."""

    rfq = models.ForeignKey(SalesRfq, on_delete=models.CASCADE, related_name="lines")
    line_number = models.PositiveIntegerField()
    part = models.ForeignKey(
        "business_core.BusinessProduct",
        on_delete=models.PROTECT,
        related_name="rfq_lines",
        blank=True,
        null=True,
    )
    material = models.ForeignKey(
        "business_core.BusinessMaterial",
        on_delete=models.PROTECT,
        related_name="rfq_lines",
        blank=True,
        null=True,
    )
    description = models.TextField()
    quantity = models.DecimalField(max_digits=16, decimal_places=4)
    unit = models.CharField(max_length=8, choices=RFQ_UNIT_CHOICES, default="PCS")
    required_delivery_date = models.DateField()
    tolerance = models.CharField(max_length=120, blank=True)
    technical_notes = models.TextField(blank=True)
    drawing_required = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sales_rfq_lines"
        ordering = ["rfq_id", "line_number"]
        constraints = [
            models.UniqueConstraint(fields=["rfq", "line_number"], name="uq_rfqline_parent_number"),
            models.CheckConstraint(condition=models.Q(line_number__gt=0), name="ck_rfqline_number_pos"),
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name="ck_rfqline_quantity_pos"),
            models.CheckConstraint(
                condition=models.Q(unit__in=[choice[0] for choice in RFQ_UNIT_CHOICES]),
                name="ck_rfqline_unit",
            ),
            models.CheckConstraint(condition=~models.Q(description=""), name="ck_rfqline_v1_required"),
        ]

    def __str__(self):
        return f"{self.rfq.rfq_number}/{self.line_number}"


class SalesRfqDocument(models.Model):
    """Versioned RFQ document metadata; binary content lives in object storage."""

    rfq = models.ForeignKey(SalesRfq, on_delete=models.CASCADE, related_name="documents")
    rfq_line = models.ForeignKey(
        SalesRfqLine,
        on_delete=models.CASCADE,
        related_name="documents",
        blank=True,
        null=True,
    )
    document_group_id = models.UUIDField(default=uuid.uuid4)
    version = models.PositiveIntegerField(default=1)
    original_filename = models.CharField(max_length=255)
    storage_key = models.CharField(max_length=512)
    mime_type = models.CharField(max_length=120, choices=RFQ_DOCUMENT_MIME_CHOICES)
    size_bytes = models.PositiveBigIntegerField()
    checksum_sha256 = models.CharField(max_length=64, db_index=True)
    document_revision = models.CharField(max_length=64, blank=True)
    replaces = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="replaced_by",
        blank=True,
        null=True,
    )
    uploaded_by = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.PROTECT,
        related_name="uploaded_rfq_documents",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sales_rfq_documents"
        ordering = ["rfq_id", "document_group_id", "version"]
        indexes = [
            models.Index(fields=["rfq", "uploaded_at"], name="sales_rfqdoc_rfq_time_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["document_group_id", "version"],
                name="uq_rfqdoc_group_version",
            ),
            models.UniqueConstraint(fields=["storage_key"], name="uq_rfqdoc_storage_key"),
            models.CheckConstraint(condition=models.Q(version__gt=0), name="ck_rfqdoc_version_pos"),
            models.CheckConstraint(condition=models.Q(size_bytes__gt=0), name="ck_rfqdoc_size_pos"),
            models.CheckConstraint(
                condition=models.Q(checksum_sha256__regex=r"^[0-9a-fA-F]{64}$"),
                name="ck_rfqdoc_checksum_len",
            ),
            models.CheckConstraint(
                condition=models.Q(mime_type__in=[choice[0] for choice in RFQ_DOCUMENT_MIME_CHOICES]),
                name="ck_rfqdoc_mime",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(original_filename="")
                    & ~models.Q(storage_key="")
                    & ~models.Q(checksum_sha256="")
                ),
                name="ck_rfqdoc_v1_required",
            ),
        ]

    def clean(self):
        """Reject cross-RFQ line links and invalid replacement chains."""
        super().clean()
        if self.rfq_line_id and self.rfq_line.rfq_id != self.rfq_id:
            raise ValidationError({"rfq_line": "The document line must belong to the same RFQ."})
        if self.replaces_id:
            if self.replaces.rfq_id != self.rfq_id:
                raise ValidationError({"replaces": "The replaced document must belong to the same RFQ."})
            if self.replaces.document_group_id != self.document_group_id:
                raise ValidationError({"replaces": "Replacement versions must remain in one document group."})
            if self.replaces.version >= self.version:
                raise ValidationError({"replaces": "A replacement must have a later version."})

    def __str__(self):
        return f"{self.original_filename} v{self.version}"


class AppendOnlyTechnicalReviewQuerySet(models.QuerySet):
    """Block bulk mutation of technical-review business evidence."""

    def update(self, **kwargs):
        raise RuntimeError("SalesTechnicalReview records are append-only.")

    def delete(self):
        raise RuntimeError("SalesTechnicalReview records are append-only.")


class SalesTechnicalReview(models.Model):
    """Append-only technical decision evidence for an RFQ."""

    rfq = models.ForeignKey(SalesRfq, on_delete=models.PROTECT, related_name="technical_reviews")
    reviewer = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.PROTECT,
        related_name="technical_reviews",
    )
    decision = models.CharField(max_length=24, choices=TECHNICAL_REVIEW_DECISION_CHOICES)
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    requested_fields = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AppendOnlyTechnicalReviewQuerySet.as_manager()

    class Meta:
        db_table = "sales_technical_reviews"
        ordering = ["rfq_id", "created_at", "id"]
        indexes = [
            models.Index(fields=["rfq", "created_at"], name="sales_techreview_rfq_time_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(decision__in=[choice[0] for choice in TECHNICAL_REVIEW_DECISION_CHOICES]),
                name="ck_techreview_decision",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(decision__in=["NEEDS_INFORMATION", "DECLINED"])
                    | ~models.Q(reason="")
                ),
                name="ck_techreview_reason",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(rfq__isnull=False)
                    & models.Q(reviewer__isnull=False)
                ),
                name="ck_techreview_v1_required",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise RuntimeError("SalesTechnicalReview records are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("SalesTechnicalReview records are append-only.")

    def __str__(self):
        return f"{self.rfq.rfq_number}: {self.decision}"
