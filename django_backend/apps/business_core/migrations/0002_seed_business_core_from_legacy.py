"""Seed Django-owned business core data from read-only legacy tables."""

from __future__ import annotations

import sqlite3
from decimal import Decimal
from pathlib import Path

from django.db import migrations
from django.utils.text import slugify


def _project_root():
    """Return the repository root from this migration file."""
    return Path(__file__).resolve().parents[4]


def _legacy_database_path():
    """Return the expected legacy SQLite database path."""
    return _project_root() / "backend" / "database" / "mecprecision.sqlite"


def _legacy_rows(query):
    """Read rows from the legacy SQLite database in read-only mode."""
    database_path = _legacy_database_path()
    if not database_path.exists():
        return []

    connection_uri = f"file:{database_path.as_posix()}?mode=ro"
    with sqlite3.connect(connection_uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(query).fetchall()]


def _safe_slug(value, fallback):
    """Create a non-empty slug for Django-owned rows."""
    return slugify(value or fallback) or fallback


def _seed_products(apps):
    """Copy legacy products into Django-owned product rows."""
    BusinessProduct = apps.get_model("business_core", "BusinessProduct")
    products = _legacy_rows(
        """
        SELECT
            products.id,
            products.category_id,
            categories.name AS category_name,
            products.name,
            products.slug,
            products.short_description,
            products.description,
            products.main_image,
            products.status,
            products.sku,
            products.price,
            products.seo_title,
            products.seo_description,
            products.seo_keywords,
            products.sort_order,
            products.published_at
        FROM products
        LEFT JOIN product_categories categories ON categories.id = products.category_id
        ORDER BY products.id
        """
    )
    for product in products:
        BusinessProduct.objects.update_or_create(
            legacy_product_id=product["id"],
            defaults={
                "legacy_category_id": product.get("category_id"),
                "category_name": product.get("category_name") or "",
                "name": product.get("name") or f"Legacy product {product['id']}",
                "slug": _safe_slug(product.get("slug") or product.get("name"), f"legacy-product-{product['id']}"),
                "sku": product.get("sku") or "",
                "price": Decimal(str(product.get("price") or 0)),
                "status": product.get("status") or "published",
                "short_description": product.get("short_description") or "",
                "description": product.get("description") or "",
                "main_image": product.get("main_image") or "",
                "seo_title": product.get("seo_title") or "",
                "seo_description": product.get("seo_description") or "",
                "seo_keywords": product.get("seo_keywords") or "",
                "sort_order": product.get("sort_order") or 0,
                "published_at": product.get("published_at") or "",
            },
        )


def _seed_customers(apps):
    """Copy legacy customers into Django-owned customer rows."""
    BusinessCustomer = apps.get_model("business_core", "BusinessCustomer")
    customers = _legacy_rows(
        """
        SELECT
            id,
            company_name,
            contact_name,
            email,
            phone,
            country
        FROM customers
        ORDER BY id
        """
    )
    for customer in customers:
        BusinessCustomer.objects.update_or_create(
            legacy_customer_id=customer["id"],
            defaults={
                "company_name": customer.get("company_name") or "",
                "contact_name": customer.get("contact_name") or f"Legacy customer {customer['id']}",
                "email": customer.get("email") or "",
                "phone": customer.get("phone") or "",
                "country": customer.get("country") or "Vietnam",
                "status": "active",
            },
        )


def _seed_inventory(apps):
    """Create demo inventory balances because legacy has no inventory table."""
    BusinessProduct = apps.get_model("business_core", "BusinessProduct")
    InventoryWarehouse = apps.get_model("business_core", "InventoryWarehouse")
    InventoryItem = apps.get_model("business_core", "InventoryItem")
    InventoryTransaction = apps.get_model("business_core", "InventoryTransaction")

    warehouse, _created = InventoryWarehouse.objects.get_or_create(
        code="MAIN",
        defaults={
            "name": "Main Demo Warehouse",
            "location": "Ho Chi Minh City",
            "is_active": True,
        },
    )
    for index, product in enumerate(BusinessProduct.objects.order_by("id")[:5], start=1):
        quantity = Decimal(index * 10)
        item, created = InventoryItem.objects.get_or_create(
            product=product,
            warehouse=warehouse,
            defaults={
                "quantity": quantity,
                "reserved_quantity": Decimal("0"),
                "reorder_point": Decimal("5"),
            },
        )
        if created:
            InventoryTransaction.objects.create(
                item=item,
                transaction_type="initial",
                quantity_delta=quantity,
                reason="Seeded inventory balance for Wave 2 demo",
            )


def seed_business_core(apps, schema_editor):
    """Seed products, customers, and inventory without changing legacy tables."""
    _seed_products(apps)
    _seed_customers(apps)
    _seed_inventory(apps)


def noop_reverse(apps, schema_editor):
    """Keep seeded rows during rollback to avoid accidental data loss."""


class Migration(migrations.Migration):

    dependencies = [
        ("business_core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_business_core, noop_reverse),
    ]
