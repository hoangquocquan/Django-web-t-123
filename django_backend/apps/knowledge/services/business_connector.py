"""Read-only business context connector for the knowledge assistant."""

from __future__ import annotations

from apps.business_core.models import BusinessCustomer, BusinessProduct, InventoryItem
from apps.transaction_domain.models import TransactionOrder


class BusinessKnowledgeConnector:
    """Expose safe read-only domain summaries for AI context."""

    def build_context(self, query):
        """Return high-level product, customer, inventory, and order context."""
        return {
            "products": self._sample(BusinessProduct, ["name", "sku", "category_name", "status"]),
            "customers": self._sample(BusinessCustomer, ["company_name", "email", "status"]),
            "inventory": self._sample_inventory(),
            "orders": self._sample(TransactionOrder, ["order_number", "project_name", "status"]),
        }

    def _sample(self, model, fields):
        """Read a tiny ORM sample without exposing unrestricted raw data."""
        rows = []
        for item in model.objects.all()[:3]:
            row = {}
            for field in fields:
                row[field] = getattr(item, field, "")
            rows.append(row)
        return rows

    def _sample_inventory(self):
        """Read safe inventory rows with product and warehouse labels."""
        rows = []
        for item in InventoryItem.objects.select_related("product", "warehouse").all()[:3]:
            rows.append(
                {
                    "product": item.product.name,
                    "warehouse": item.warehouse.code,
                    "quantity": str(item.quantity),
                    "reserved_quantity": str(item.reserved_quantity),
                }
            )
        return rows


class PublicBusinessKnowledgeConnector:
    """Expose only published-style product facts to the public assistant."""

    def build_context(self, query):
        """Return a bounded product catalogue without private business records."""
        del query
        products = []
        for product in BusinessProduct.objects.filter(is_active=True).order_by("id")[:5]:
            products.append(
                {
                    "name": product.name,
                    "category": getattr(product, "category_name", "") or "",
                    "material": getattr(product, "material", "") or "",
                    "description": getattr(product, "short_description", "") or "",
                }
            )
        return {"products": products}
