"""Django-owned transaction domain API views."""

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.api.serializers.transaction_domain import (
    OrderCreateSerializer,
    OrderUpdateSerializer,
    WorkflowTransitionSerializer,
    approval_to_dict,
    order_detail_to_dict,
    order_to_dict,
    transaction_history_to_dict,
)
from apps.api.views.foundation import _require_foundation_permission
from apps.api.views.helpers import handle_not_found, ok, paginated_ok
from apps.transaction_domain.services import (
    OrderService,
    TransactionHistoryService,
    WorkflowService,
)


def _permission_response(exc):
    """Return JSON for permission failures."""
    return Response(
        {
            "success": False,
            "error": {
                "code": "permission_denied",
                "message": str(exc),
            },
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def _validation_response(exc):
    """Return JSON for validation failures."""
    messages = getattr(exc, "messages", [str(exc)])
    return Response(
        {
            "success": False,
            "error": {
                "code": "validation_error",
                "message": "; ".join(str(message) for message in messages),
            },
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET", "POST"])
def orders(request):
    """List or create Django-owned orders."""
    try:
        action = "write" if request.method == "POST" else "read"
        user = _require_foundation_permission(request, "orders", action)
    except PermissionDenied as exc:
        return _permission_response(exc)

    service = OrderService()
    if request.method == "GET":
        return paginated_ok(request, service.list_orders(), order_to_dict)

    serializer = OrderCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        order = service.create_order(**serializer.validated_data, actor=user.email)
    except (ObjectDoesNotExist, ValidationError) as exc:
        return _validation_response(exc)
    return Response({"success": True, "data": order_detail_to_dict(service.get_order(order.id))}, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT"])
def order_detail(request, order_id):
    """Read or update one Django-owned order."""
    try:
        action = "write" if request.method == "PUT" else "read"
        user = _require_foundation_permission(request, "orders", action)
    except PermissionDenied as exc:
        return _permission_response(exc)

    service = OrderService()

    def execute():
        order = service.get_order(order_id)
        if request.method == "GET":
            return ok(order_detail_to_dict(order))
        serializer = OrderUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = service.update_order(order, **serializer.validated_data, actor=user.email)
        return ok(order_detail_to_dict(service.get_order(updated.id)))

    return handle_not_found("Order", execute)


@api_view(["GET", "POST"])
def workflows(request):
    """List approvals or transition an order workflow."""
    try:
        action = "write" if request.method == "POST" else "read"
        user = _require_foundation_permission(request, "workflows", action)
    except PermissionDenied as exc:
        return _permission_response(exc)

    service = WorkflowService()
    if request.method == "GET":
        return paginated_ok(request, service.list_approvals(), approval_to_dict)

    serializer = WorkflowTransitionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        order = OrderService().get_order(serializer.validated_data["order_id"])
        transitioned = service.transition_order(
            order=order,
            target_status=serializer.validated_data["target_status"],
            actor=user.email,
            note=serializer.validated_data.get("note", ""),
        )
    except (ObjectDoesNotExist, ValidationError) as exc:
        return _validation_response(exc)
    return ok(order_detail_to_dict(OrderService().get_order(transitioned.id)))


@api_view(["GET"])
def transactions(request):
    """List Django-owned transaction history."""
    try:
        _require_foundation_permission(request, "transactions", "read")
    except PermissionDenied as exc:
        return _permission_response(exc)

    return paginated_ok(request, TransactionHistoryService().list_history(), transaction_history_to_dict)
