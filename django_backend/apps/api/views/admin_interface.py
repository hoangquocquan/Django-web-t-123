"""Django-owned admin dashboard APIs.

This module is the migration target for admin operations. It intentionally uses
Django-owned models and services only, and does not call legacy `backend/*`
services or repositories.
"""

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.db.models import F, Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.api.admin_query import apply_admin_query
from apps.api.serializers.admin_interface import (
    BusinessCustomerSerializer,
    BusinessCustomerUpdateSerializer,
    BusinessProductSerializer,
    BusinessProductUpdateSerializer,
    FoundationLoginSerializer,
    InventoryAdjustmentSerializer,
    InventoryItemSerializer,
    InventoryWarehouseSerializer,
    OrderCreateSerializer,
    OrderUpdateSerializer,
    WorkflowTransitionSerializer,
    admin_navigation_to_dict,
    business_customer_to_dict,
    business_product_to_dict,
    inventory_item_to_dict,
    order_detail_to_dict,
    order_to_dict,
    role_to_dict,
    transaction_history_to_dict,
    user_to_dict,
    warehouse_to_dict,
)
from apps.api.services.admin_dashboard_service import AdminDashboardQueryService
from apps.api.views.foundation import _require_foundation_permission
from apps.api.views.helpers import handle_not_found, ok, paginated_ok
from apps.business_core.services import (
    VALID_CUSTOMER_STATUSES,
    VALID_PRODUCT_STATUSES,
    BusinessCustomerService,
    BusinessProductService,
    InventoryService,
)
from apps.foundation.services import FoundationAuthService, FoundationPermissionService
from apps.transaction_domain.services import (
    VALID_ORDER_STATUSES,
    OrderService,
    TransactionHistoryService,
    WorkflowService,
)


def _permission_response(exc):
    """Return JSON for admin permission failures."""
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
    """Return JSON for admin validation failures."""
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


def _admin_user(request, module, action="read"):
    """Authenticate an admin request and enforce the required permission."""
    return _require_foundation_permission(request, module, action)


def _boolean_filter(field_name):
    """Build a strict boolean filter for one endpoint-owned model field."""

    def apply(queryset, value):
        normalized = value.lower()
        if normalized not in {"true", "false"}:
            raise ValueError("Boolean filters must be `true` or `false`.")
        return queryset.filter(**{field_name: normalized == "true"})

    return apply


def _choice_filter(field_name, allowed_values):
    """Build an exact case-insensitive filter constrained to known values."""
    normalized_values = {value.lower() for value in allowed_values}

    def apply(queryset, value):
        normalized = value.lower()
        if normalized not in normalized_values:
            raise ValueError(f"Unsupported `{field_name}` value.")
        return queryset.filter(**{f"{field_name}__iexact": normalized})

    return apply


def _material_filter(queryset, value):
    """Filter products by material code or material name."""
    return queryset.filter(
        Q(default_material__material_code__iexact=value)
        | Q(default_material__name__icontains=value)
    )


def _warehouse_filter(queryset, value):
    """Filter inventory by a numeric warehouse id or exact warehouse code."""
    if value.isdigit():
        return queryset.filter(warehouse_id=int(value))
    return queryset.filter(warehouse__code__iexact=value)


def _availability_filter(queryset, value):
    """Filter stock by positive or zero computed availability."""
    normalized = value.lower()
    if normalized == "positive":
        return queryset.filter(quantity__gt=F("reserved_quantity"))
    if normalized == "zero":
        return queryset.filter(quantity__lte=F("reserved_quantity"))
    raise ValueError("`availability` must be `positive` or `zero`.")


@api_view(["POST"])
@permission_classes([AllowAny])
def admin_login(request):
    """Create an admin token using Django-owned foundation authentication."""
    serializer = FoundationLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        raw_token, token = FoundationAuthService().login(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            remote_addr=request.META.get("REMOTE_ADDR", ""),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
    except PermissionDenied as exc:
        return _permission_response(exc)

    return ok(
        {
            "token": raw_token,
            "expires_at": token.expires_at.isoformat(),
            "user": user_to_dict(token.user),
            "navigation": admin_navigation_to_dict(),
        }
    )


@api_view(["GET"])
def admin_dashboard(request):
    """Return Django-owned admin dashboard counters."""
    try:
        user = _admin_user(request, "dashboard", "read")
    except PermissionDenied as exc:
        return _permission_response(exc)

    return ok(
        {
            "user": user_to_dict(user),
            "navigation": admin_navigation_to_dict(),
            "metrics": AdminDashboardQueryService().metrics(),
            "ownership": "django",
        }
    )


@api_view(["GET"])
def admin_permissions(request):
    """Return Django-owned roles and permissions for admin management."""
    try:
        _admin_user(request, "permissions", "read")
    except PermissionDenied as exc:
        return _permission_response(exc)

    permission_service = FoundationPermissionService()
    roles = permission_service.list_roles()
    return ok([role_to_dict(role, permission_service) for role in roles])


@api_view(["GET", "POST"])
def admin_products(request):
    """List or create products through Django-owned services."""
    try:
        _admin_user(
            request, "products", "write" if request.method == "POST" else "read"
        )
    except PermissionDenied as exc:
        return _permission_response(exc)

    service = BusinessProductService()
    if request.method == "GET":
        queryset, error_response = apply_admin_query(
            request,
            service.list_products(),
            search_fields=(
                "part_code",
                "sku",
                "name",
                "default_material__material_code",
                "default_material__name",
            ),
            filters={
                "status": _choice_filter("status", VALID_PRODUCT_STATUSES),
                "active": _boolean_filter("is_active"),
                "material": _material_filter,
            },
            ordering_fields={
                "created_at": "created_at",
                "product_code": "part_code",
                "name": "name",
            },
        )
        if error_response:
            return error_response
        return paginated_ok(request, queryset, business_product_to_dict)

    serializer = BusinessProductSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        product = service.create_product(**serializer.validated_data)
    except ValidationError as exc:
        return _validation_response(exc)
    return Response(
        {"success": True, "data": business_product_to_dict(product)},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PUT"])
def admin_product_detail(request, product_id):
    """Read or update one product through Django-owned services."""
    try:
        _admin_user(request, "products", "write" if request.method == "PUT" else "read")
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
            updated = service.update_product(product, **serializer.validated_data)
        except ValidationError as exc:
            return _validation_response(exc)
        return ok(business_product_to_dict(updated))

    return handle_not_found("Admin product", execute)


@api_view(["GET", "POST"])
def admin_customers(request):
    """List or create customers through Django-owned services."""
    try:
        _admin_user(
            request, "customers", "write" if request.method == "POST" else "read"
        )
    except PermissionDenied as exc:
        return _permission_response(exc)

    service = BusinessCustomerService()
    if request.method == "GET":
        queryset, error_response = apply_admin_query(
            request,
            service.list_customers(),
            search_fields=("company_name", "contact_name"),
            filters={
                "status": _choice_filter("status", VALID_CUSTOMER_STATUSES),
            },
            ordering_fields={
                "created_at": "created_at",
                "company_name": "company_name",
                "contact_name": "contact_name",
            },
        )
        if error_response:
            return error_response
        return paginated_ok(request, queryset, business_customer_to_dict)

    serializer = BusinessCustomerSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        customer = service.create_customer(**serializer.validated_data)
    except ValidationError as exc:
        return _validation_response(exc)
    return Response(
        {"success": True, "data": business_customer_to_dict(customer)},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PUT"])
def admin_customer_detail(request, customer_id):
    """Read or update one customer through Django-owned services."""
    try:
        _admin_user(
            request, "customers", "write" if request.method == "PUT" else "read"
        )
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
            updated = service.update_customer(customer, **serializer.validated_data)
        except ValidationError as exc:
            return _validation_response(exc)
        return ok(business_customer_to_dict(updated))

    return handle_not_found("Admin customer", execute)


@api_view(["GET", "POST"])
def admin_inventory_warehouses(request):
    """List or create warehouses through Django-owned inventory service."""
    try:
        _admin_user(
            request, "inventory", "write" if request.method == "POST" else "read"
        )
    except PermissionDenied as exc:
        return _permission_response(exc)

    service = InventoryService()
    if request.method == "GET":
        return paginated_ok(request, service.list_warehouses(), warehouse_to_dict)

    serializer = InventoryWarehouseSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    warehouse = service.create_warehouse(**serializer.validated_data)
    return Response(
        {"success": True, "data": warehouse_to_dict(warehouse)},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "POST"])
def admin_inventory_items(request):
    """List or create stock balances through Django-owned inventory service."""
    try:
        _admin_user(
            request, "inventory", "write" if request.method == "POST" else "read"
        )
    except PermissionDenied as exc:
        return _permission_response(exc)

    service = InventoryService()
    if request.method == "GET":
        queryset, error_response = apply_admin_query(
            request,
            service.list_items(),
            search_fields=(
                "product__name",
                "product__default_material__material_code",
                "product__default_material__name",
            ),
            filters={
                "warehouse": _warehouse_filter,
                "availability": _availability_filter,
            },
            ordering_fields={
                "quantity": "quantity",
                "updated_at": "updated_at",
            },
        )
        if error_response:
            return error_response
        return paginated_ok(request, queryset, inventory_item_to_dict)

    serializer = InventoryItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        product = service.get_product(serializer.validated_data["product_id"])
        warehouse = service.get_warehouse(serializer.validated_data["warehouse_id"])
        item = service.create_item(
            product=product,
            warehouse=warehouse,
            quantity=serializer.validated_data.get("quantity", 0),
            reorder_point=serializer.validated_data.get("reorder_point", 0),
        )
    except ObjectDoesNotExist as exc:
        return _validation_response(exc)
    return Response(
        {"success": True, "data": inventory_item_to_dict(item)},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
def admin_inventory_adjust(request, item_id):
    """Adjust inventory stock through Django-owned inventory service."""
    try:
        user = _admin_user(request, "inventory", "write")
    except PermissionDenied as exc:
        return _permission_response(exc)

    serializer = InventoryAdjustmentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    service = InventoryService()

    def execute():
        item = service.get_item(item_id)
        try:
            updated = service.adjust_stock(
                item=item,
                quantity_delta=serializer.validated_data["quantity_delta"],
                transaction_type=serializer.validated_data.get(
                    "transaction_type", "adjustment"
                ),
                reason=serializer.validated_data.get("reason", ""),
                reference=serializer.validated_data.get("reference", ""),
                created_by=user.email,
            )
        except ValidationError as exc:
            return _validation_response(exc)
        return ok(inventory_item_to_dict(updated))

    return handle_not_found("Admin inventory item", execute)


@api_view(["GET", "POST"])
def admin_orders(request):
    """List or create orders through Django-owned transaction services."""
    try:
        user = _admin_user(
            request, "orders", "write" if request.method == "POST" else "read"
        )
    except PermissionDenied as exc:
        return _permission_response(exc)

    service = OrderService()
    if request.method == "GET":
        queryset, error_response = apply_admin_query(
            request,
            service.list_orders(),
            search_fields=(
                "order_number",
                "customer__company_name",
                "customer__contact_name",
            ),
            filters={
                "workflow_status": _choice_filter(
                    "workflow_status",
                    {"CONFIRMED", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELLED"},
                ),
                "status": _choice_filter("status", VALID_ORDER_STATUSES),
            },
            ordering_fields={
                "order_date": "ordered_at",
                "expected_delivery_date": "expected_delivery_date",
            },
        )
        if error_response:
            return error_response
        return paginated_ok(request, queryset, order_to_dict)

    serializer = OrderCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        order = service.create_order(**serializer.validated_data, actor=user.email)
    except (ObjectDoesNotExist, ValidationError) as exc:
        return _validation_response(exc)
    return Response(
        {"success": True, "data": order_detail_to_dict(service.get_order(order.id))},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PUT"])
def admin_order_detail(request, order_id):
    """Read or update one order through Django-owned transaction services."""
    try:
        user = _admin_user(
            request, "orders", "write" if request.method == "PUT" else "read"
        )
    except PermissionDenied as exc:
        return _permission_response(exc)

    service = OrderService()

    def execute():
        order = service.get_order(order_id)
        if request.method == "GET":
            return ok(order_detail_to_dict(order))
        serializer = OrderUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = service.update_order(
            order, **serializer.validated_data, actor=user.email
        )
        return ok(order_detail_to_dict(service.get_order(updated.id)))

    return handle_not_found("Admin order", execute)


@api_view(["GET", "POST"])
def admin_workflows(request):
    """List approvals or transition order workflow through Django services."""
    try:
        user = _admin_user(
            request, "workflows", "write" if request.method == "POST" else "read"
        )
    except PermissionDenied as exc:
        return _permission_response(exc)

    service = WorkflowService()
    if request.method == "GET":
        queryset, error_response = apply_admin_query(
            request,
            service.list_approvals(),
            search_fields=(
                "order__order_number",
                "requested_by",
                "reviewed_by",
                "note",
            ),
            filters={
                "decision": _choice_filter(
                    "decision", {"pending", "approved", "rejected"}
                ),
                "requested_status": _choice_filter(
                    "requested_status", VALID_ORDER_STATUSES
                ),
            },
            ordering_fields={"created_at": "created_at", "order": "order_id"},
        )
        if error_response:
            return error_response
        return paginated_ok(
            request,
            queryset,
            lambda approval: {
                "id": approval.id,
                "order_id": approval.order_id,
                "requested_status": approval.requested_status,
                "decision": approval.decision,
                "requested_by": approval.requested_by,
                "reviewed_by": approval.reviewed_by,
                "note": approval.note,
            },
        )

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
def admin_transactions(request):
    """List transaction history through Django-owned transaction history service."""
    try:
        _admin_user(request, "transactions", "read")
    except PermissionDenied as exc:
        return _permission_response(exc)

    queryset, error_response = apply_admin_query(
        request,
        TransactionHistoryService().list_history(),
        search_fields=("entity_id", "action", "actor"),
        filters={
            "entity_type": "entity_type__iexact",
            "action": "action__iexact",
        },
        ordering_fields={"created_at": "created_at"},
    )
    if error_response:
        return error_response
    return paginated_ok(request, queryset, transaction_history_to_dict)
