"""Service layer for Django-owned order, workflow, and transaction history logic."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.business_core.models import BusinessCustomer, BusinessProduct, InventoryItem
from apps.business_core.services import InventoryService

from .models import (
    OrderStatusHistory,
    TransactionHistory,
    TransactionOrder,
    TransactionOrderItem,
    WorkflowApproval,
)


VALID_ORDER_STATUSES = {"new", "approved", "processing", "completed", "cancelled"}
ALLOWED_TRANSITIONS = {
    "new": {"approved", "cancelled"},
    "approved": {"processing", "cancelled"},
    "processing": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}
APPROVAL_REQUIRED_STATUSES = {"approved", "cancelled"}


def _decimal(value, field_name):
    """Convert numeric API input into Decimal."""
    try:
        return Decimal(str(value or 0))
    except Exception as exc:  # noqa: BLE001 - normalize all Decimal parsing errors.
        raise ValidationError(f"{field_name} must be a valid number.") from exc


def _order_number(order_id):
    """Create a stable human-readable order number."""
    return f"ORD-{int(order_id):06d}"


class TransactionHistoryService:
    """Write append-only transaction history records."""

    def list_history(self):
        """Return all transaction history rows."""
        return TransactionHistory.objects.select_related("order").all()

    def record(self, *, order=None, entity_type, entity_id="", action, actor="", payload=None):
        """Create one audit record."""
        return TransactionHistory.objects.create(
            order=order,
            entity_type=entity_type,
            entity_id=str(entity_id or ""),
            action=action,
            actor=actor or "",
            payload=payload or {},
        )


class OrderService:
    """Own order creation and updates in Django."""

    def __init__(self, history_service=None, inventory_service=None):
        """Allow tests to inject service doubles."""
        self.history_service = history_service or TransactionHistoryService()
        self.inventory_service = inventory_service or InventoryService()

    def list_orders(self):
        """Return orders with customer and assigned user loaded."""
        return TransactionOrder.objects.select_related("customer", "assigned_to").all()

    def get_order(self, order_id):
        """Return one order with related customer."""
        return self.list_orders().get(id=order_id)

    @transaction.atomic
    def create_order(self, *, customer_id, project_name="", message="", items=None, actor=""):
        """Create an order, items, inventory reservations, and audit history atomically."""
        customer = BusinessCustomer.objects.get(id=customer_id)
        order = TransactionOrder.objects.create(
            customer=customer,
            order_number="PENDING",
            project_name=project_name or "",
            message=message or "",
            status="new",
        )
        order.order_number = _order_number(order.id)
        order.save(update_fields=["order_number"])

        total_amount = Decimal("0")
        for item_payload in items or []:
            product = None
            inventory_item = None
            if item_payload.get("product_id"):
                product = BusinessProduct.objects.get(id=item_payload["product_id"])
            if item_payload.get("inventory_item_id"):
                inventory_item = InventoryItem.objects.select_related("product", "warehouse").get(
                    id=item_payload["inventory_item_id"]
                )
                quantity = int(item_payload.get("quantity") or 1)
                self.inventory_service.adjust_stock(
                    item=inventory_item,
                    quantity_delta=Decimal(quantity) * Decimal("-1"),
                    transaction_type="reserve",
                    reason=f"Reserved for {order.order_number}",
                    reference=order.order_number,
                    created_by=actor,
                )
            quantity = int(item_payload.get("quantity") or 1)
            unit_price = _decimal(item_payload.get("unit_price", 0), "unit_price")
            line_total = unit_price * Decimal(quantity)
            total_amount += line_total
            TransactionOrderItem.objects.create(
                order=order,
                product=product,
                inventory_item=inventory_item,
                drawing_code=item_payload.get("drawing_code", "") or "",
                material_name=item_payload.get("material_name", "") or "",
                quantity=quantity,
                tolerance=item_payload.get("tolerance", "") or "",
                note=item_payload.get("note", "") or "",
                unit_price=unit_price,
                line_total=line_total,
            )

        order.total_amount = total_amount
        order.save(update_fields=["total_amount"])
        OrderStatusHistory.objects.create(order=order, to_status="new", actor=actor, note="Order created")
        self.history_service.record(
            order=order,
            entity_type="order",
            entity_id=order.id,
            action="order.created",
            actor=actor,
            payload={"order_number": order.order_number, "item_count": len(items or [])},
        )
        return order

    @transaction.atomic
    def update_order(self, order, **fields):
        """Update non-payment order metadata."""
        editable_fields = {"project_name", "message", "internal_note"}
        for field_name, value in fields.items():
            if field_name in editable_fields:
                setattr(order, field_name, value or "")
        order.save()
        self.history_service.record(
            order=order,
            entity_type="order",
            entity_id=order.id,
            action="order.updated",
            actor=fields.get("actor", ""),
            payload={key: value for key, value in fields.items() if key in editable_fields},
        )
        return order


class WorkflowService:
    """Own order status transitions and approvals in Django."""

    def __init__(self, history_service=None):
        """Allow tests to inject service doubles."""
        self.history_service = history_service or TransactionHistoryService()

    def list_approvals(self):
        """Return workflow approval rows."""
        return WorkflowApproval.objects.select_related("order").all()

    @transaction.atomic
    def transition_order(self, order, target_status, actor="", note=""):
        """Move an order to a new status and create audit records."""
        if target_status not in VALID_ORDER_STATUSES:
            raise ValidationError("Invalid order status.")
        allowed_targets = ALLOWED_TRANSITIONS.get(order.status, set())
        if target_status not in allowed_targets:
            raise ValidationError(f"Cannot transition from {order.status} to {target_status}.")

        previous_status = order.status
        approval = None
        if target_status in APPROVAL_REQUIRED_STATUSES:
            approval = WorkflowApproval.objects.create(
                order=order,
                requested_status=target_status,
                decision="approved",
                requested_by=actor,
                reviewed_by=actor,
                note=note or "",
                decided_at=timezone.now(),
            )

        order.status = target_status
        if target_status == "completed":
            order.completed_at = timezone.now().isoformat()
        order.save()
        OrderStatusHistory.objects.create(
            order=order,
            from_status=previous_status,
            to_status=target_status,
            actor=actor,
            note=note or "",
        )
        self.history_service.record(
            order=order,
            entity_type="workflow",
            entity_id=order.id,
            action="workflow.transition",
            actor=actor,
            payload={
                "from_status": previous_status,
                "to_status": target_status,
                "approval_id": approval.id if approval else None,
            },
        )
        return order
