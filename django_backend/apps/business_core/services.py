"""Service layer for Django-owned product, customer, and inventory logic."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import (
    BusinessCustomer,
    BusinessProduct,
    InventoryItem,
    InventoryTransaction,
    InventoryWarehouse,
)


VALID_PRODUCT_STATUSES = {"draft", "published", "archived"}
VALID_CUSTOMER_STATUSES = {"active", "inactive", "lead"}
VALID_TRANSACTION_TYPES = {"initial", "adjustment", "receipt", "issue", "reserve", "release"}


def _decimal(value, field_name):
    """Convert numeric API input into Decimal for database-safe math."""
    try:
        return Decimal(str(value))
    except Exception as exc:  # noqa: BLE001 - normalize all Decimal parsing errors.
        raise ValidationError(f"{field_name} must be a valid number.") from exc


class BusinessProductService:
    """Own product writes in Django while preserving legacy references."""

    def list_products(self):
        """Return Django-owned products."""
        return BusinessProduct.objects.all()

    def get_product(self, product_id):
        """Return one Django-owned product."""
        return self.list_products().get(id=product_id)

    @transaction.atomic
    def create_product(self, **fields):
        """Create one Django-owned product with validation."""
        status = fields.get("status", "draft") or "draft"
        if status not in VALID_PRODUCT_STATUSES:
            raise ValidationError("Product status must be draft, published, or archived.")
        if BusinessProduct.objects.filter(slug=fields["slug"]).exists():
            raise ValidationError("Product slug already exists.")
        fields["status"] = status
        fields["price"] = _decimal(fields.get("price", 0), "price")
        return BusinessProduct.objects.create(**fields)

    @transaction.atomic
    def update_product(self, product, **fields):
        """Update editable Django-owned product fields."""
        editable_fields = {
            "legacy_category_id",
            "category_name",
            "name",
            "sku",
            "price",
            "status",
            "short_description",
            "description",
            "main_image",
            "seo_title",
            "seo_description",
            "seo_keywords",
            "sort_order",
            "published_at",
        }
        if "status" in fields and fields["status"] not in VALID_PRODUCT_STATUSES:
            raise ValidationError("Product status must be draft, published, or archived.")
        if "price" in fields:
            fields["price"] = _decimal(fields["price"], "price")
        for field_name, value in fields.items():
            if field_name in editable_fields:
                setattr(product, field_name, value)
        product.save()
        return product


class BusinessCustomerService:
    """Own customer writes in Django while legacy CRM remains readable."""

    def list_customers(self):
        """Return Django-owned customers."""
        return BusinessCustomer.objects.all()

    def get_customer(self, customer_id):
        """Return one Django-owned customer."""
        return self.list_customers().get(id=customer_id)

    @transaction.atomic
    def create_customer(self, **fields):
        """Create one Django-owned customer with validation."""
        status = fields.get("status", "active") or "active"
        if status not in VALID_CUSTOMER_STATUSES:
            raise ValidationError("Customer status must be active, inactive, or lead.")
        fields["status"] = status
        return BusinessCustomer.objects.create(**fields)

    @transaction.atomic
    def update_customer(self, customer, **fields):
        """Update editable Django-owned customer fields."""
        editable_fields = {
            "company_name",
            "contact_name",
            "email",
            "phone",
            "country",
            "status",
            "notes",
        }
        if "status" in fields and fields["status"] not in VALID_CUSTOMER_STATUSES:
            raise ValidationError("Customer status must be active, inactive, or lead.")
        for field_name, value in fields.items():
            if field_name in editable_fields:
                setattr(customer, field_name, value)
        customer.save()
        return customer


class InventoryService:
    """Own inventory stock movements with transaction safety."""

    def list_warehouses(self):
        """Return active and inactive warehouses."""
        return InventoryWarehouse.objects.all()

    def list_items(self):
        """Return stock balances with product and warehouse loaded."""
        return InventoryItem.objects.select_related("product", "warehouse").all()

    def get_item(self, item_id):
        """Return one stock balance."""
        return self.list_items().get(id=item_id)

    @transaction.atomic
    def create_warehouse(self, code, name, location="", is_active=True):
        """Create one Django-owned warehouse."""
        return InventoryWarehouse.objects.create(
            code=code,
            name=name,
            location=location or "",
            is_active=is_active,
        )

    @transaction.atomic
    def create_item(self, product, warehouse, quantity=0, reorder_point=0):
        """Create one stock balance and initial transaction."""
        quantity_value = _decimal(quantity, "quantity")
        item = InventoryItem.objects.create(
            product=product,
            warehouse=warehouse,
            quantity=quantity_value,
            reorder_point=_decimal(reorder_point, "reorder_point"),
        )
        InventoryTransaction.objects.create(
            item=item,
            transaction_type="initial",
            quantity_delta=quantity_value,
            reason="Initial stock balance",
        )
        return item

    @transaction.atomic
    def adjust_stock(self, item, quantity_delta, transaction_type="adjustment", reason="", reference="", created_by=""):
        """Adjust stock and rollback automatically if validation fails."""
        if transaction_type not in VALID_TRANSACTION_TYPES:
            raise ValidationError("Invalid inventory transaction type.")
        delta = _decimal(quantity_delta, "quantity_delta")
        locked_item = InventoryItem.objects.select_for_update().get(id=item.id)
        new_quantity = locked_item.quantity + delta
        if new_quantity < 0:
            raise ValidationError("Inventory quantity cannot become negative.")
        locked_item.quantity = new_quantity
        locked_item.save()
        InventoryTransaction.objects.create(
            item=locked_item,
            transaction_type=transaction_type,
            quantity_delta=delta,
            reason=reason or "",
            reference=reference or "",
            created_by=created_by or "",
        )
        return locked_item
