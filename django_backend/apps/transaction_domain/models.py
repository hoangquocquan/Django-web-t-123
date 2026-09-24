"""Managed models for legacy transactions and canonical Phase 3D orders."""

from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.db import models


DATA_CONTRACT_CHOICES = [("LEGACY", "Legacy"), ("MVP_V1", "MVP V1")]
ORDER_WORKFLOW_STATUS_CHOICES = [
    ("CONFIRMED", "Confirmed"),
    ("IN_PROGRESS", "In progress"),
    ("ON_HOLD", "On hold"),
    ("COMPLETED", "Completed"),
    ("CANCELLED", "Cancelled"),
]
ORDER_UNIT_CHOICES = [
    ("PCS", "Pieces"),
    ("KG", "Kilograms"),
    ("M", "Metres"),
    ("MM", "Millimetres"),
]
AUDIT_ACTIONS = {
    "customer.created",
    "customer.updated",
    "customer.archived",
    "rfq.created",
    "rfq.updated",
    "rfq.submitted",
    "rfq.resubmitted",
    "rfq.technical_review_started",
    "rfq.information_requested",
    "rfq.review_completed",
    "rfq.declined",
    "rfq.closed",
    "rfq.document_uploaded",
    "rfq.document_versioned",
    "quotation.created",
    "quotation.revision_created",
    "quotation.submitted",
    "quotation.approved",
    "quotation.rejected",
    "quotation.sent",
    "quotation.customer_accepted",
    "quotation.customer_declined",
    "quotation.expired",
    "quotation.superseded",
    "order.converted",
    "order.progress_changed",
    "order.held",
    "order.resumed",
    "order.completed",
    "order.cancelled",
}
UNSAFE_METADATA_KEY_FRAGMENTS = {
    "address",
    "authorization",
    "contact",
    "cookie",
    "credential",
    "customer_snapshot",
    "document_content",
    "email",
    "full_name",
    "password",
    "passwd",
    "phone",
    "quotation_snapshot",
    "secret",
    "session",
    "token",
}


def validate_safe_audit_metadata(value, *, path="metadata", depth=0):
    """Reject secrets, unnecessary PII, binary values, and unbounded metadata."""
    if depth > 4:
        raise ValidationError({"metadata": "Audit metadata nesting is too deep."})
    if value is None or isinstance(value, (bool, int, float)):
        return
    if isinstance(value, str):
        if len(value) > 500:
            raise ValidationError({"metadata": f"{path} exceeds the safe length."})
        return
    if isinstance(value, list):
        if len(value) > 50:
            raise ValidationError({"metadata": f"{path} contains too many values."})
        for index, item in enumerate(value):
            validate_safe_audit_metadata(item, path=f"{path}[{index}]", depth=depth + 1)
        return
    if isinstance(value, dict):
        if len(value) > 50:
            raise ValidationError({"metadata": f"{path} contains too many keys."})
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValidationError({"metadata": "Audit metadata keys must be strings."})
            normalized = key.casefold()
            if any(fragment in normalized for fragment in UNSAFE_METADATA_KEY_FRAGMENTS):
                raise ValidationError({"metadata": f"Unsafe audit metadata key: {key}."})
            validate_safe_audit_metadata(item, path=f"{path}.{key}", depth=depth + 1)
        return
    raise ValidationError({"metadata": f"Unsupported audit metadata value at {path}."})


class TransactionOrderQuerySet(models.QuerySet):
    """Prevent bulk mutation or deletion of canonical order evidence."""

    PROTECTED_FIELDS = {
        "data_contract", "source_quotation", "source_quotation_id", "source_rfq",
        "source_rfq_id", "customer", "customer_id", "order_number", "workflow_status",
        "currency", "subtotal", "discount_total", "tax_amount", "total_amount",
        "customer_snapshot", "quotation_snapshot", "ordered_at", "expected_delivery_date",
        "progress_percent", "hold_reason", "cancel_reason", "source_quotation_sent_at",
        "completed_at_v1", "idempotency_key", "request_hash", "created_by",
        "created_by_id", "updated_by", "updated_by_id",
    }

    def update(self, **kwargs):
        if self.filter(data_contract="MVP_V1").exists() and self.PROTECTED_FIELDS.intersection(kwargs):
            raise RuntimeError("Canonical sales orders may change only through Phase 3D commands.")
        return super().update(**kwargs)

    def delete(self):
        if self.filter(data_contract="MVP_V1").exists():
            raise RuntimeError("Canonical sales orders cannot be deleted.")
        return super().delete()

    def bulk_create(
        self, objs, batch_size=None, ignore_conflicts=False, update_conflicts=False,
        update_fields=None, unique_fields=None,
    ):
        if any(item.data_contract == "MVP_V1" for item in objs):
            raise RuntimeError("MVP_V1 sales orders must be created by quotation conversion.")
        return super().bulk_create(
            objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts,
            update_conflicts=update_conflicts, update_fields=update_fields,
            unique_fields=unique_fields,
        )


class TransactionOrder(models.Model):
    """Canonical Sales Order header extended in-place from the legacy model."""

    legacy_quote_request_id = models.IntegerField(blank=True, null=True, unique=True)
    order_number = models.CharField(max_length=80, unique=True)
    customer = models.ForeignKey(
        "business_core.BusinessCustomer", on_delete=models.PROTECT, related_name="orders"
    )
    project_name = models.CharField(max_length=220, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=40, default="new")
    assigned_to = models.ForeignKey(
        "foundation.FoundationUser", on_delete=models.SET_NULL,
        related_name="assigned_orders", blank=True, null=True,
    )
    internal_note = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    quoted_at = models.CharField(max_length=80, blank=True)
    completed_at = models.CharField(max_length=80, blank=True)
    data_contract = models.CharField(
        max_length=16, choices=DATA_CONTRACT_CHOICES, default="LEGACY", db_index=True,
    )
    source_quotation = models.ForeignKey(
        "sales.SalesQuotation", on_delete=models.PROTECT, related_name="sales_orders",
        blank=True, null=True,
    )
    source_rfq = models.ForeignKey(
        "sales.SalesRfq", on_delete=models.PROTECT, related_name="sales_orders",
        blank=True, null=True,
    )
    workflow_status = models.CharField(
        max_length=16, choices=ORDER_WORKFLOW_STATUS_CHOICES,
        blank=True, null=True, db_index=True,
    )
    currency = models.CharField(
        max_length=3, choices=[("VND", "Vietnamese dong"), ("USD", "US dollar")],
        blank=True, null=True,
    )
    subtotal = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    discount_total = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    tax_amount = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    customer_snapshot = models.JSONField(default=dict, blank=True)
    quotation_snapshot = models.JSONField(default=dict, blank=True)
    ordered_at = models.DateTimeField(blank=True, null=True)
    expected_delivery_date = models.DateField(blank=True, null=True)
    progress_percent = models.PositiveSmallIntegerField(default=0)
    hold_reason = models.TextField(blank=True)
    cancel_reason = models.TextField(blank=True)
    source_quotation_sent_at = models.DateTimeField(blank=True, null=True)
    completed_at_v1 = models.DateTimeField(blank=True, null=True)
    idempotency_key = models.CharField(max_length=64, blank=True, null=True)
    request_hash = models.CharField(max_length=64, blank=True)
    created_by = models.ForeignKey(
        "foundation.FoundationUser", on_delete=models.PROTECT,
        related_name="created_transaction_orders", blank=True, null=True,
    )
    updated_by = models.ForeignKey(
        "foundation.FoundationUser", on_delete=models.PROTECT,
        related_name="updated_transaction_orders", blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TransactionOrderQuerySet.as_manager()

    IMMUTABLE_V1_FIELDS = (
        "data_contract", "source_quotation_id", "source_rfq_id", "customer_id",
        "order_number", "currency", "subtotal", "discount_total", "tax_amount",
        "total_amount", "customer_snapshot", "quotation_snapshot", "ordered_at",
        "expected_delivery_date", "source_quotation_sent_at", "idempotency_key",
        "request_hash", "created_by_id",
    )
    COMMAND_FIELDS = (
        "workflow_status", "progress_percent", "hold_reason", "cancel_reason",
        "completed_at_v1", "updated_by_id",
    )

    class Meta:
        db_table = "transaction_orders"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status"], name="transaction_order_status_idx"),
            models.Index(fields=["legacy_quote_request_id"], name="transaction_order_legacy_idx"),
            models.Index(fields=["source_rfq"], name="tx_order_source_rfq_idx"),
            models.Index(fields=["workflow_status", "expected_delivery_date"], name="tx_order_flow_date_idx"),
            models.Index(fields=["ordered_at"], name="tx_order_ordered_idx"),
            models.Index(fields=["created_by"], name="tx_order_creator_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source_quotation"], condition=models.Q(source_quotation__isnull=False),
                name="uq_order_source_quote",
            ),
            models.UniqueConstraint(
                fields=["idempotency_key"], condition=models.Q(idempotency_key__isnull=False),
                name="uq_order_idempotency_nonnull",
            ),
            models.CheckConstraint(
                condition=(~models.Q(data_contract="MVP_V1") | models.Q(
                    workflow_status__in=[item[0] for item in ORDER_WORKFLOW_STATUS_CHOICES]
                )), name="ck_order_workflow_status",
            ),
            models.CheckConstraint(
                condition=(~models.Q(data_contract="MVP_V1") | (
                    models.Q(source_quotation__isnull=False)
                    & models.Q(source_rfq__isnull=False)
                    & models.Q(workflow_status__isnull=False)
                    & models.Q(currency__isnull=False)
                    & models.Q(ordered_at__isnull=False)
                    & models.Q(expected_delivery_date__isnull=False)
                    & models.Q(idempotency_key__isnull=False)
                    & models.Q(created_by__isnull=False)
                    & ~models.Q(order_number="")
                    & ~models.Q(request_hash="")
                )), name="ck_order_v1_required",
            ),
            models.CheckConstraint(
                condition=~models.Q(data_contract="MVP_V1") | models.Q(currency__in=["VND", "USD"]),
                name="ck_order_currency",
            ),
            models.CheckConstraint(
                condition=(~models.Q(data_contract="MVP_V1") | (
                    models.Q(subtotal__gte=0) & models.Q(discount_total__gte=0)
                    & models.Q(tax_amount__gte=0) & models.Q(total_amount__gte=0)
                )), name="ck_order_money_nonneg",
            ),
            models.CheckConstraint(
                condition=~models.Q(data_contract="MVP_V1") | models.Q(discount_total__lte=models.F("subtotal")),
                name="ck_order_discount_bound",
            ),
            models.CheckConstraint(
                condition=(~models.Q(data_contract="MVP_V1") | models.Q(
                    total_amount=models.F("subtotal") - models.F("discount_total") + models.F("tax_amount")
                )), name="ck_order_total_equation",
            ),
            models.CheckConstraint(
                condition=models.Q(progress_percent__gte=0, progress_percent__lte=100),
                name="ck_order_progress_range",
            ),
            models.CheckConstraint(
                condition=(~models.Q(data_contract="MVP_V1", workflow_status="ON_HOLD") | ~models.Q(hold_reason="")),
                name="ck_order_hold_reason",
            ),
            models.CheckConstraint(
                condition=(~models.Q(data_contract="MVP_V1", workflow_status="CANCELLED") | ~models.Q(cancel_reason="")),
                name="ck_order_cancel_reason",
            ),
            models.CheckConstraint(
                condition=(models.Q(idempotency_key__isnull=True, request_hash="") | (
                    models.Q(idempotency_key__isnull=False) & ~models.Q(request_hash="")
                )), name="ck_order_idempotency_pair",
            ),
            models.CheckConstraint(
                condition=(models.Q(idempotency_key__isnull=True) | models.Q(
                    request_hash__regex=r"^[0-9a-fA-F]{64}$"
                )), name="ck_order_request_hash",
            ),
        ]

    def clean(self):
        super().clean()
        if self.data_contract != "MVP_V1":
            return
        if not self.customer_snapshot or not self.quotation_snapshot:
            raise ValidationError("Canonical sales orders require customer and quotation snapshots.")
        if self.ordered_at and self.expected_delivery_date:
            if self.expected_delivery_date < self.ordered_at.date():
                raise ValidationError({"expected_delivery_date": "Delivery cannot precede the order date."})
        if self.workflow_status == "COMPLETED" and self.completed_at_v1 is None:
            raise ValidationError({"completed_at_v1": "Completed orders require a completion timestamp."})

    def save(self, *args, **kwargs):
        if self._state.adding and self.data_contract == "MVP_V1":
            if not getattr(self, "_phase3d_conversion_authorized", False):
                raise RuntimeError("MVP_V1 sales orders must be created by quotation conversion.")
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).values(
                "data_contract", *self.IMMUTABLE_V1_FIELDS, *self.COMMAND_FIELDS
            ).first()
            if previous and previous["data_contract"] == "MVP_V1":
                if any(previous[field] != getattr(self, field) for field in self.IMMUTABLE_V1_FIELDS):
                    raise RuntimeError("Canonical sales-order commercial snapshots are immutable.")
                command_changed = any(previous[field] != getattr(self, field) for field in self.COMMAND_FIELDS)
                if command_changed and not getattr(self, "_phase3d_transition_authorized", False):
                    raise RuntimeError("Canonical order progress may change only through Phase 3D commands.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.data_contract == "MVP_V1":
            raise RuntimeError("Canonical sales orders cannot be deleted.")
        return super().delete(*args, **kwargs)

    def __str__(self):
        return self.order_number


class TransactionOrderItemQuerySet(models.QuerySet):
    """Keep canonical order-line snapshots immutable."""

    def _contains_v1(self):
        return self.filter(data_contract="MVP_V1").exists()

    def update(self, **kwargs):
        if self._contains_v1():
            raise RuntimeError("Canonical sales-order lines are immutable.")
        return super().update(**kwargs)

    def delete(self):
        if self._contains_v1():
            raise RuntimeError("Canonical sales-order lines are immutable.")
        return super().delete()

    def bulk_update(self, objs, fields, batch_size=None):
        if any(item.data_contract == "MVP_V1" for item in objs):
            raise RuntimeError("Canonical sales-order lines are immutable.")
        return super().bulk_update(objs, fields, batch_size=batch_size)

    def bulk_create(
        self, objs, batch_size=None, ignore_conflicts=False, update_conflicts=False,
        update_fields=None, unique_fields=None,
    ):
        if any(item.data_contract == "MVP_V1" for item in objs):
            raise RuntimeError("MVP_V1 order lines must be created by quotation conversion.")
        return super().bulk_create(
            objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts,
            update_conflicts=update_conflicts, update_fields=update_fields,
            unique_fields=unique_fields,
        )


class TransactionOrderItem(models.Model):
    """Immutable commercial line snapshot extended from the legacy order item."""

    legacy_quote_item_id = models.IntegerField(blank=True, null=True, unique=True)
    order = models.ForeignKey(TransactionOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "business_core.BusinessProduct", on_delete=models.PROTECT,
        related_name="order_items", blank=True, null=True,
    )
    inventory_item = models.ForeignKey(
        "business_core.InventoryItem", on_delete=models.PROTECT,
        related_name="order_items", blank=True, null=True,
    )
    drawing_code = models.CharField(max_length=160, blank=True)
    material_name = models.CharField(max_length=160, blank=True)
    quantity = models.DecimalField(max_digits=16, decimal_places=4, default=1)
    tolerance = models.CharField(max_length=120, blank=True)
    note = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    line_total = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    data_contract = models.CharField(
        max_length=16, choices=DATA_CONTRACT_CHOICES, default="LEGACY", db_index=True,
    )
    line_number = models.PositiveIntegerField(blank=True, null=True)
    source_quotation_line = models.ForeignKey(
        "sales.SalesQuotationLine", on_delete=models.PROTECT,
        related_name="order_lines", blank=True, null=True,
    )
    description_snapshot = models.TextField(blank=True)
    part_code_snapshot = models.CharField(max_length=32, blank=True)
    material_snapshot = models.CharField(max_length=240, blank=True)
    unit = models.CharField(max_length=8, choices=ORDER_UNIT_CHOICES, blank=True)

    objects = TransactionOrderItemQuerySet.as_manager()

    class Meta:
        db_table = "transaction_order_items"
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "line_number"], condition=models.Q(line_number__isnull=False),
                name="uq_orderline_parent_number",
            ),
            models.UniqueConstraint(
                fields=["source_quotation_line"], condition=models.Q(source_quotation_line__isnull=False),
                name="uq_orderline_source_line",
            ),
            models.CheckConstraint(
                condition=models.Q(line_number__isnull=True) | models.Q(line_number__gt=0),
                name="ck_orderline_number_pos",
            ),
            models.CheckConstraint(
                condition=~models.Q(data_contract="MVP_V1") | models.Q(quantity__gt=0),
                name="ck_orderline_quantity_pos",
            ),
            models.CheckConstraint(
                condition=~models.Q(data_contract="MVP_V1") | (
                    models.Q(unit_price__gte=0) & models.Q(line_total__gte=0)
                ), name="ck_orderline_money_nonneg",
            ),
            models.CheckConstraint(
                condition=models.Q(unit="") | models.Q(unit__in=[item[0] for item in ORDER_UNIT_CHOICES]),
                name="ck_orderline_unit",
            ),
            models.CheckConstraint(
                condition=~models.Q(data_contract="MVP_V1") | (
                    models.Q(line_number__isnull=False)
                    & models.Q(source_quotation_line__isnull=False)
                    & ~models.Q(description_snapshot="")
                    & ~models.Q(part_code_snapshot="")
                    & ~models.Q(unit="")
                ), name="ck_orderline_v1_required",
            ),
        ]

    def clean(self):
        super().clean()
        if self.data_contract == "MVP_V1" and self.source_quotation_line_id:
            if self.order.source_quotation_id != self.source_quotation_line.quotation_id:
                raise ValidationError({"source_quotation_line": "Source line must belong to the order quotation."})

    def save(self, *args, **kwargs):
        if self._state.adding and self.data_contract == "MVP_V1":
            if not getattr(self, "_phase3d_conversion_authorized", False):
                raise RuntimeError("MVP_V1 order lines must be created by quotation conversion.")
        if self.pk and type(self).objects.filter(pk=self.pk, data_contract="MVP_V1").exists():
            raise RuntimeError("Canonical sales-order lines are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.data_contract == "MVP_V1":
            raise RuntimeError("Canonical sales-order lines are immutable.")
        return super().delete(*args, **kwargs)

    def __str__(self):
        return self.description_snapshot or self.drawing_code or f"Order item #{self.id}"


class OrderStatusHistory(models.Model):
    """Retained legacy status history; not rewritten into canonical progress."""

    order = models.ForeignKey(TransactionOrder, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=40, blank=True)
    to_status = models.CharField(max_length=40)
    actor = models.CharField(max_length=160, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_status_history"
        ordering = ["-created_at", "-id"]


class WorkflowApproval(models.Model):
    """Retained legacy workflow approval; never treated as quotation evidence."""

    order = models.ForeignKey(TransactionOrder, on_delete=models.CASCADE, related_name="approvals")
    requested_status = models.CharField(max_length=40)
    decision = models.CharField(max_length=40, default="pending")
    requested_by = models.CharField(max_length=160, blank=True)
    reviewed_by = models.CharField(max_length=160, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "workflow_approvals"
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["decision"], name="workflow_approval_decision_idx")]


class TransactionHistory(models.Model):
    """Retained fragmented historic log; canonical writes use AuditEvent."""

    legacy_event_id = models.IntegerField(blank=True, null=True, unique=True)
    order = models.ForeignKey(
        TransactionOrder, on_delete=models.SET_NULL, related_name="transaction_history",
        blank=True, null=True,
    )
    entity_type = models.CharField(max_length=80)
    entity_id = models.CharField(max_length=80, blank=True)
    action = models.CharField(max_length=120)
    actor = models.CharField(max_length=160, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transaction_history"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"], name="transaction_history_entity_idx"),
            models.Index(fields=["action"], name="transaction_history_action_idx"),
        ]


class AppendOnlyEvidenceQuerySet(models.QuerySet):
    """Block all queryset mutation for canonical event evidence."""

    message = "Canonical event records are append-only."

    def update(self, **kwargs):
        raise RuntimeError(self.message)

    def delete(self):
        raise RuntimeError(self.message)

    def bulk_update(self, objs, fields, batch_size=None):
        raise RuntimeError(self.message)

    def bulk_create(
        self, objs, batch_size=None, ignore_conflicts=False, update_conflicts=False,
        update_fields=None, unique_fields=None,
    ):
        for obj in objs:
            obj.full_clean()
        return super().bulk_create(
            objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts,
            update_conflicts=update_conflicts, update_fields=update_fields,
            unique_fields=unique_fields,
        )


class OrderProgressEvent(models.Model):
    """Append-only canonical order progress evidence."""

    order = models.ForeignKey(TransactionOrder, on_delete=models.PROTECT, related_name="progress_events")
    from_status = models.CharField(max_length=16, blank=True)
    to_status = models.CharField(max_length=16, choices=ORDER_WORKFLOW_STATUS_CHOICES)
    progress_percent = models.PositiveSmallIntegerField()
    milestone_note = models.CharField(max_length=240, blank=True)
    reason = models.TextField(blank=True)
    actor = models.ForeignKey(
        "foundation.FoundationUser", on_delete=models.PROTECT,
        related_name="order_progress_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AppendOnlyEvidenceQuerySet.as_manager()

    class Meta:
        db_table = "transaction_order_progress_events"
        ordering = ["order_id", "created_at", "id"]
        indexes = [
            models.Index(fields=["order", "created_at"], name="tx_progress_order_time_idx"),
            models.Index(fields=["to_status", "created_at"], name="tx_progress_status_time_idx"),
            models.Index(fields=["actor", "created_at"], name="tx_progress_actor_time_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=((models.Q(from_status="") | models.Q(
                    from_status__in=[item[0] for item in ORDER_WORKFLOW_STATUS_CHOICES]
                )) & models.Q(to_status__in=[item[0] for item in ORDER_WORKFLOW_STATUS_CHOICES])),
                name="ck_progress_statuses",
            ),
            models.CheckConstraint(
                condition=models.Q(progress_percent__gte=0, progress_percent__lte=100),
                name="ck_progress_percent_range",
            ),
            models.CheckConstraint(
                condition=~models.Q(to_status__in=["ON_HOLD", "CANCELLED"]) | ~models.Q(reason=""),
                name="ck_progress_reason",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise RuntimeError("Order progress events are append-only.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Order progress events are append-only.")


class AuditEvent(models.Model):
    """Append-only canonical audit record with safe structured metadata."""

    actor_ref = models.CharField(max_length=80)
    actor_display = models.CharField(max_length=160)
    actor_user = models.ForeignKey(
        "foundation.FoundationUser", on_delete=models.PROTECT,
        related_name="audit_events", blank=True, null=True,
    )
    action = models.CharField(max_length=120)
    entity_type = models.CharField(max_length=80)
    entity_id = models.CharField(max_length=80)
    old_status = models.CharField(max_length=24, blank=True)
    new_status = models.CharField(max_length=24, blank=True)
    reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    correlation_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AppendOnlyEvidenceQuerySet.as_manager()

    class Meta:
        db_table = "transaction_audit_events"
        ordering = ["entity_type", "entity_id", "created_at", "id"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id", "created_at"], name="tx_audit_entity_time_idx"),
            models.Index(fields=["action", "created_at"], name="tx_audit_action_time_idx"),
            models.Index(fields=["actor_ref", "created_at"], name="tx_audit_actor_time_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(actor_ref="") & ~models.Q(actor_display=""),
                name="ck_audit_actor_ref",
            ),
            models.CheckConstraint(
                condition=~models.Q(action="") & ~models.Q(entity_type="") & ~models.Q(entity_id=""),
                name="ck_audit_required",
            ),
        ]

    def clean(self):
        super().clean()
        if self.action not in AUDIT_ACTIONS:
            raise ValidationError({"action": "Action is not in the Phase 3D audit catalog."})
        if self.actor_ref == "system":
            if self.actor_user_id is not None:
                raise ValidationError({"actor_user": "System events cannot reference a fake user."})
        elif self.actor_user_id is None or self.actor_ref != f"user:{self.actor_user_id}":
            raise ValidationError({"actor_ref": "Human events require the matching stable user reference."})
        validate_safe_audit_metadata(self.metadata)

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise RuntimeError("Audit events are append-only.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Audit events are append-only.")
