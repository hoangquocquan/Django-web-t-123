"""Django-owned business core API views."""

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.api.serializers.business_core import (
    BusinessCustomerSerializer,
    BusinessCustomerUpdateSerializer,
    BusinessProductSerializer,
    BusinessProductUpdateSerializer,
    InventoryAdjustmentSerializer,
    InventoryItemSerializer,
    InventoryWarehouseSerializer,
    business_customer_to_dict,
    business_product_to_dict,
    inventory_item_to_dict,
    warehouse_to_dict,
)
from apps.api.views.foundation import _require_foundation_permission
from apps.api.views.helpers import handle_not_found, ok, paginated_ok
from apps.business_core.models import BusinessProduct, InventoryWarehouse
from apps.business_core.services import (
    BusinessCustomerService,
    BusinessProductService,
    InventoryService,
)


def _permission_response(exc):
    """Return JSON for authentication or authorization failures."""
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
    """Return JSON for service validation failures."""
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
def business_products(request):
    """List or create Django-owned products."""
    try:
        action = "write" if request.method == "POST" else "read"
        _require_foundation_permission(request, "products", action)
    except PermissionDenied as exc:
        return _permission_response(exc)

    service = BusinessProductService()
    if request.method == "GET":
        return paginated_ok(request, service.list_products(), business_product_to_dict)

    serializer = BusinessProductSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        product = service.create_product(**serializer.validated_data)
    except ValidationError as exc:
        return _validation_response(exc)
    return Response({"success": True, "data": business_product_to_dict(product)}, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT"])
def business_product_detail(request, product_id):
    """Read or update one Django-owned product."""
    try:
        action = "write" if request.method == "PUT" else "read"
        _require_foundation_permission(request, "products", action)
    except PermissionDenied as exc:
        return _permission_response(exc)

    service = BusinessProductService()

    def execute():
        product = service.get_product(product_id)
        if request.method == "GET":
            return ok(business_product_to_dict(product))
        serializer = BusinessProductUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            updated_product = service.update_product(product, **serializer.validated_data)
        except ValidationError as exc:
            return _validation_response(exc)
        return ok(business_product_to_dict(updated_product))

    return handle_not_found("Business product", execute)


@api_view(["GET", "POST"])
def business_customers(request):
    """List or create Django-owned customers."""
    try:
        action = "write" if request.method == "POST" else "read"
        _require_foundation_permission(request, "customers", action)
    except PermissionDenied as exc:
        return _permission_response(exc)

    service = BusinessCustomerService()
    if request.method == "GET":
        return paginated_ok(request, service.list_customers(), business_customer_to_dict)

    serializer = BusinessCustomerSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        customer = service.create_customer(**serializer.validated_data)
    except ValidationError as exc:
        return _validation_response(exc)
    return Response({"success": True, "data": business_customer_to_dict(customer)}, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT"])
def business_customer_detail(request, customer_id):
    """Read or update one Django-owned customer."""
    try:
        action = "write" if request.method == "PUT" else "read"
        _require_foundation_permission(request, "customers", action)
    except PermissionDenied as exc:
        return _permission_response(exc)

    service = BusinessCustomerService()

    def execute():
        customer = service.get_customer(customer_id)
        if request.method == "GET":
            return ok(business_customer_to_dict(customer))
        serializer = BusinessCustomerUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            updated_customer = service.update_customer(customer, **serializer.validated_data)
        except ValidationError as exc:
            return _validation_response(exc)
        return ok(business_customer_to_dict(updated_customer))

    return handle_not_found("Business customer", execute)


@api_view(["GET", "POST"])
def inventory_warehouses(request):
    """List or create Django-owned warehouses."""
    try:
        action = "write" if request.method == "POST" else "read"
        _require_foundation_permission(request, "inventory", action)
    except PermissionDenied as exc:
        return _permission_response(exc)

    service = InventoryService()
    if request.method == "GET":
        return paginated_ok(request, service.list_warehouses(), warehouse_to_dict)

    serializer = InventoryWarehouseSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    warehouse = service.create_warehouse(**serializer.validated_data)
    return Response({"success": True, "data": warehouse_to_dict(warehouse)}, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
def inventory_items(request):
    """List or create Django-owned inventory balances."""
    try:
        action = "write" if request.method == "POST" else "read"
        _require_foundation_permission(request, "inventory", action)
    except PermissionDenied as exc:
        return _permission_response(exc)

    service = InventoryService()
    if request.method == "GET":
        return paginated_ok(request, service.list_items(), inventory_item_to_dict)

    serializer = InventoryItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        product = BusinessProduct.objects.get(id=serializer.validated_data["product_id"])
        warehouse = InventoryWarehouse.objects.get(id=serializer.validated_data["warehouse_id"])
    except ObjectDoesNotExist:
        return Response(
            {
                "success": False,
                "error": {
                    "code": "not_found",
                    "message": "Product or warehouse was not found.",
                },
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    item = service.create_item(
        product=product,
        warehouse=warehouse,
        quantity=serializer.validated_data.get("quantity", 0),
        reorder_point=serializer.validated_data.get("reorder_point", 0),
    )
    return Response({"success": True, "data": inventory_item_to_dict(item)}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def inventory_adjust(request, item_id):
    """Apply one stock movement to a Django-owned inventory item."""
    try:
        user = _require_foundation_permission(request, "inventory", "write")
    except PermissionDenied as exc:
        return _permission_response(exc)

    serializer = InventoryAdjustmentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    service = InventoryService()

    def execute():
        item = service.get_item(item_id)
        try:
            updated_item = service.adjust_stock(
                item=item,
                quantity_delta=serializer.validated_data["quantity_delta"],
                transaction_type=serializer.validated_data.get("transaction_type", "adjustment"),
                reason=serializer.validated_data.get("reason", ""),
                reference=serializer.validated_data.get("reference", ""),
                created_by=user.email,
            )
        except ValidationError as exc:
            return _validation_response(exc)
        return ok(inventory_item_to_dict(updated_item))

    return handle_not_found("Inventory item", execute)
