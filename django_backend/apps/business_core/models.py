"""Managed Django models for product, customer, and inventory ownership."""

from django.db import models


class BusinessProduct(models.Model):
    """Django-owned product record copied gradually from legacy catalog data."""

    legacy_product_id = models.IntegerField(blank=True, null=True, unique=True)
    legacy_category_id = models.IntegerField(blank=True, null=True)
    category_name = models.CharField(max_length=160, blank=True)
    name = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True)
    sku = models.CharField(max_length=120, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=30, default="draft")
    short_description = models.TextField(blank=True)
    description = models.TextField(blank=True)
    main_image = models.TextField(blank=True)
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True)
    seo_keywords = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)
    published_at = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "business_products"
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(fields=["status"], name="business_product_status_idx"),
            models.Index(fields=["legacy_category_id"], name="business_product_cat_idx"),
        ]

    def __str__(self):
        """Return product name for admin/debug output."""
        return self.name


class BusinessCustomer(models.Model):
    """Django-owned customer record copied gradually from legacy CRM data."""

    legacy_customer_id = models.IntegerField(blank=True, null=True, unique=True)
    company_name = models.CharField(max_length=220, blank=True)
    contact_name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=80, blank=True)
    country = models.CharField(max_length=120, default="Vietnam", blank=True)
    status = models.CharField(max_length=40, default="active")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "business_customers"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["email"], name="business_customer_email_idx"),
            models.Index(fields=["status"], name="business_customer_status_idx"),
        ]

    def __str__(self):
        """Return the most useful customer display name."""
        return self.company_name or self.contact_name


class InventoryWarehouse(models.Model):
    """Django-owned warehouse or stock location."""

    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=160)
    location = models.CharField(max_length=220, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inventory_warehouses"
        ordering = ["code"]

    def __str__(self):
        """Return warehouse code and name."""
        return f"{self.code} - {self.name}"


class InventoryItem(models.Model):
    """Django-owned stock balance for one product in one warehouse."""

    product = models.ForeignKey(
        BusinessProduct,
        on_delete=models.PROTECT,
        related_name="inventory_items",
    )
    warehouse = models.ForeignKey(
        InventoryWarehouse,
        on_delete=models.PROTECT,
        related_name="items",
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reserved_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_point = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_items"
        unique_together = [("product", "warehouse")]
        ordering = ["product_id", "warehouse_id"]
        indexes = [
            models.Index(fields=["product", "warehouse"], name="inventory_item_product_wh_idx"),
        ]

    def __str__(self):
        """Return a compact stock balance label."""
        return f"{self.product_id}@{self.warehouse.code}: {self.quantity}"


class InventoryTransaction(models.Model):
    """Append-only inventory movement used to audit stock changes."""

    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    transaction_type = models.CharField(max_length=40)
    quantity_delta = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField(blank=True)
    reference = models.CharField(max_length=120, blank=True)
    created_by = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inventory_transactions"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["transaction_type"], name="inventory_tx_type_idx"),
        ]

    def __str__(self):
        """Return transaction type and quantity."""
        return f"{self.transaction_type}: {self.quantity_delta}"
