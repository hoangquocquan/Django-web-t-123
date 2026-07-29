"""Managed Django models for order, workflow, and transaction history ownership."""

from django.db import models


class TransactionOrder(models.Model):
    """Django-owned order header, seeded from legacy quote requests when available."""

    legacy_quote_request_id = models.IntegerField(blank=True, null=True, unique=True)
    order_number = models.CharField(max_length=80, unique=True)
    customer = models.ForeignKey(
        "business_core.BusinessCustomer",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    project_name = models.CharField(max_length=220, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=40, default="new")
    assigned_to = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.SET_NULL,
        related_name="assigned_orders",
        blank=True,
        null=True,
    )
    internal_note = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    quoted_at = models.CharField(max_length=80, blank=True)
    completed_at = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transaction_orders"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status"], name="transaction_order_status_idx"),
            models.Index(fields=["legacy_quote_request_id"], name="transaction_order_legacy_idx"),
        ]

    def __str__(self):
        """Return the order number."""
        return self.order_number


class TransactionOrderItem(models.Model):
    """Django-owned order line item."""

    legacy_quote_item_id = models.IntegerField(blank=True, null=True, unique=True)
    order = models.ForeignKey(TransactionOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "business_core.BusinessProduct",
        on_delete=models.PROTECT,
        related_name="order_items",
        blank=True,
        null=True,
    )
    inventory_item = models.ForeignKey(
        "business_core.InventoryItem",
        on_delete=models.PROTECT,
        related_name="order_items",
        blank=True,
        null=True,
    )
    drawing_code = models.CharField(max_length=160, blank=True)
    material_name = models.CharField(max_length=160, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    tolerance = models.CharField(max_length=120, blank=True)
    note = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = "transaction_order_items"
        ordering = ["id"]

    def __str__(self):
        """Return a compact line-item label."""
        return self.drawing_code or f"Order item #{self.id}"


class OrderStatusHistory(models.Model):
    """Append-only status transition history for an order."""

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
    """Django-owned approval record for important workflow transitions."""

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
        indexes = [
            models.Index(fields=["decision"], name="workflow_approval_decision_idx"),
        ]


class TransactionHistory(models.Model):
    """Django-owned audit/event log for transaction-domain operations."""

    legacy_event_id = models.IntegerField(blank=True, null=True, unique=True)
    order = models.ForeignKey(
        TransactionOrder,
        on_delete=models.SET_NULL,
        related_name="transaction_history",
        blank=True,
        null=True,
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
