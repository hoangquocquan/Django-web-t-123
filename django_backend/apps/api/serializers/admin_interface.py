"""Serializers for the Django-owned admin interface APIs."""

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
from apps.api.serializers.foundation import FoundationLoginSerializer, role_to_dict, user_to_dict
from apps.api.serializers.transaction_domain import (
    OrderCreateSerializer,
    OrderUpdateSerializer,
    WorkflowTransitionSerializer,
    order_detail_to_dict,
    order_to_dict,
    transaction_history_to_dict,
)


def admin_navigation_to_dict():
    """Return the Django-owned admin navigation structure."""
    return [
        {"module": "dashboard", "label": "Dashboard", "path": "/api/v1/admin/dashboard/"},
        {"module": "products", "label": "Products", "path": "/api/v1/admin/products/"},
        {"module": "customers", "label": "Customers", "path": "/api/v1/admin/customers/"},
        {"module": "inventory", "label": "Inventory", "path": "/api/v1/admin/inventory/items/"},
        {"module": "orders", "label": "Orders", "path": "/api/v1/admin/orders/"},
        {"module": "workflows", "label": "Workflows", "path": "/api/v1/admin/workflows/"},
        {"module": "transactions", "label": "Transactions", "path": "/api/v1/admin/transactions/"},
        {"module": "permissions", "label": "Permissions", "path": "/api/v1/admin/permissions/"},
    ]
