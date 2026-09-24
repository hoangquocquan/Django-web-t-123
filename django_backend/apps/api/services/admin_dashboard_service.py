"""Read-only query service for Django admin dashboard metrics."""

from apps.business_core.models import BusinessCustomer, BusinessProduct, InventoryItem
from apps.transaction_domain.models import (
    TransactionHistory,
    TransactionOrder,
    WorkflowApproval,
)


class AdminDashboardQueryService:
    """Keep ORM aggregation outside the API presentation layer."""

    def metrics(self):
        return {
            "products": BusinessProduct.objects.count(),
            "customers": BusinessCustomer.objects.count(),
            "inventory_items": InventoryItem.objects.count(),
            "orders": TransactionOrder.objects.count(),
            "workflow_approvals": WorkflowApproval.objects.count(),
            "transaction_history": TransactionHistory.objects.count(),
        }
