"""Serializers for Django-owned transaction domain APIs."""

from rest_framework import serializers


class OrderItemSerializer(serializers.Serializer):
    """Validate one order line item payload."""

    product_id = serializers.IntegerField(required=False, allow_null=True)
    inventory_item_id = serializers.IntegerField(required=False, allow_null=True)
    drawing_code = serializers.CharField(required=False, allow_blank=True, max_length=160)
    material_name = serializers.CharField(required=False, allow_blank=True, max_length=160)
    quantity = serializers.IntegerField(default=1, min_value=1)
    tolerance = serializers.CharField(required=False, allow_blank=True, max_length=120)
    note = serializers.CharField(required=False, allow_blank=True)
    unit_price = serializers.DecimalField(required=False, max_digits=12, decimal_places=2)


class OrderCreateSerializer(serializers.Serializer):
    """Validate order creation payloads."""

    customer_id = serializers.IntegerField()
    project_name = serializers.CharField(required=False, allow_blank=True, max_length=220)
    message = serializers.CharField(required=False, allow_blank=True)
    items = OrderItemSerializer(many=True, required=False)


class OrderUpdateSerializer(serializers.Serializer):
    """Validate safe non-payment order update fields."""

    project_name = serializers.CharField(required=False, allow_blank=True, max_length=220)
    message = serializers.CharField(required=False, allow_blank=True)
    internal_note = serializers.CharField(required=False, allow_blank=True)


class WorkflowTransitionSerializer(serializers.Serializer):
    """Validate order workflow transition requests."""

    order_id = serializers.IntegerField()
    target_status = serializers.CharField(max_length=40)
    note = serializers.CharField(required=False, allow_blank=True)


def order_item_to_dict(item):
    """Convert an order item to API JSON."""
    return {
        "id": item.id,
        "legacy_quote_item_id": item.legacy_quote_item_id,
        "product_id": item.product_id,
        "inventory_item_id": item.inventory_item_id,
        "drawing_code": item.drawing_code,
        "material_name": item.material_name,
        "quantity": item.quantity,
        "tolerance": item.tolerance,
        "note": item.note,
        "unit_price": str(item.unit_price),
        "line_total": str(item.line_total),
    }


def order_to_dict(order):
    """Convert a Django-owned order to API JSON."""
    return {
        "id": order.id,
        "legacy_quote_request_id": order.legacy_quote_request_id,
        "order_number": order.order_number,
        "customer_id": order.customer_id,
        "customer_name": str(order.customer),
        "project_name": order.project_name,
        "message": order.message,
        "status": order.status,
        "assigned_to_id": order.assigned_to_id,
        "internal_note": order.internal_note,
        "total_amount": str(order.total_amount),
        "quoted_at": order.quoted_at,
        "completed_at": order.completed_at,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
    }


def order_detail_to_dict(order):
    """Convert an order and its related rows to API JSON."""
    data = order_to_dict(order)
    data["items"] = [order_item_to_dict(item) for item in order.items.all()]
    data["status_history"] = [
        {
            "id": history.id,
            "from_status": history.from_status,
            "to_status": history.to_status,
            "actor": history.actor,
            "note": history.note,
            "created_at": history.created_at.isoformat() if history.created_at else None,
        }
        for history in order.status_history.all()
    ]
    return data


def approval_to_dict(approval):
    """Convert a workflow approval to API JSON."""
    return {
        "id": approval.id,
        "order_id": approval.order_id,
        "requested_status": approval.requested_status,
        "decision": approval.decision,
        "requested_by": approval.requested_by,
        "reviewed_by": approval.reviewed_by,
        "note": approval.note,
        "created_at": approval.created_at.isoformat() if approval.created_at else None,
        "decided_at": approval.decided_at.isoformat() if approval.decided_at else None,
    }


def transaction_history_to_dict(history):
    """Convert transaction history to API JSON."""
    return {
        "id": history.id,
        "legacy_event_id": history.legacy_event_id,
        "order_id": history.order_id,
        "entity_type": history.entity_type,
        "entity_id": history.entity_id,
        "action": history.action,
        "actor": history.actor,
        "payload": history.payload,
        "created_at": history.created_at.isoformat() if history.created_at else None,
    }
