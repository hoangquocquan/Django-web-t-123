"""Seed Django-owned transaction domain data from legacy quote/event tables."""

from __future__ import annotations

import json
import sqlite3
from decimal import Decimal
from pathlib import Path

from django.db import migrations


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


def _order_number(legacy_quote_id):
    """Create a stable order number for a legacy quote."""
    return f"ORD-LQ-{int(legacy_quote_id):06d}"


def _json_payload(value):
    """Parse legacy JSON payload safely."""
    try:
        return json.loads(value or "{}")
    except json.JSONDecodeError:
        return {"raw": value or ""}


def _seed_orders(apps):
    """Copy legacy quote requests and quote items into order tables."""
    BusinessCustomer = apps.get_model("business_core", "BusinessCustomer")
    BusinessProduct = apps.get_model("business_core", "BusinessProduct")
    TransactionOrder = apps.get_model("transaction_domain", "TransactionOrder")
    TransactionOrderItem = apps.get_model("transaction_domain", "TransactionOrderItem")
    OrderStatusHistory = apps.get_model("transaction_domain", "OrderStatusHistory")
    TransactionHistory = apps.get_model("transaction_domain", "TransactionHistory")

    quotes = _legacy_rows(
        """
        SELECT
            id,
            customer_id,
            project_name,
            message,
            status,
            assigned_to,
            internal_note,
            quoted_at,
            completed_at
        FROM quote_requests
        ORDER BY id
        """
    )
    for quote in quotes:
        customer = BusinessCustomer.objects.filter(legacy_customer_id=quote["customer_id"]).first()
        if not customer:
            continue
        order, created = TransactionOrder.objects.update_or_create(
            legacy_quote_request_id=quote["id"],
            defaults={
                "customer": customer,
                "order_number": _order_number(quote["id"]),
                "project_name": quote.get("project_name") or "",
                "message": quote.get("message") or "",
                "status": quote.get("status") or "new",
                "internal_note": quote.get("internal_note") or "",
                "quoted_at": quote.get("quoted_at") or "",
                "completed_at": quote.get("completed_at") or "",
            },
        )
        if created:
            OrderStatusHistory.objects.create(
                order=order,
                to_status=order.status,
                actor="legacy-import",
                note="Imported from legacy quote request",
            )
            TransactionHistory.objects.create(
                order=order,
                entity_type="order",
                entity_id=str(order.id),
                action="order.imported",
                actor="legacy-import",
                payload={"legacy_quote_request_id": quote["id"]},
            )

    items = _legacy_rows(
        """
        SELECT
            items.id,
            items.quote_request_id,
            items.product_id,
            items.drawing_code,
            items.material_id,
            materials.name AS material_name,
            items.quantity,
            items.tolerance,
            items.note
        FROM quote_request_items items
        LEFT JOIN materials materials ON materials.id = items.material_id
        ORDER BY items.id
        """
    )
    for item in items:
        order = TransactionOrder.objects.filter(legacy_quote_request_id=item["quote_request_id"]).first()
        if not order:
            continue
        product = None
        if item.get("product_id"):
            product = BusinessProduct.objects.filter(legacy_product_id=item["product_id"]).first()
        quantity = item.get("quantity") or 1
        TransactionOrderItem.objects.update_or_create(
            legacy_quote_item_id=item["id"],
            defaults={
                "order": order,
                "product": product,
                "drawing_code": item.get("drawing_code") or "",
                "material_name": item.get("material_name") or "",
                "quantity": quantity,
                "tolerance": item.get("tolerance") or "",
                "note": item.get("note") or "",
                "unit_price": Decimal("0"),
                "line_total": Decimal("0"),
            },
        )


def _seed_transaction_history(apps):
    """Copy legacy enterprise events into Django-owned transaction history."""
    TransactionHistory = apps.get_model("transaction_domain", "TransactionHistory")
    events = _legacy_rows(
        """
        SELECT
            id,
            event_name,
            entity_type,
            entity_id,
            payload,
            status
        FROM enterprise_events
        ORDER BY id
        """
    )
    for event in events:
        TransactionHistory.objects.update_or_create(
            legacy_event_id=event["id"],
            defaults={
                "entity_type": event.get("entity_type") or "legacy_event",
                "entity_id": event.get("entity_id") or "",
                "action": event.get("event_name") or "legacy.event",
                "actor": "legacy-import",
                "payload": {
                    "status": event.get("status") or "",
                    "payload": _json_payload(event.get("payload")),
                },
            },
        )


def seed_transaction_domain(apps, schema_editor):
    """Seed transaction domain without changing legacy tables."""
    _seed_orders(apps)
    _seed_transaction_history(apps)


def noop_reverse(apps, schema_editor):
    """Keep imported rows during rollback to avoid accidental data loss."""


class Migration(migrations.Migration):

    dependencies = [
        ("business_core", "0002_seed_business_core_from_legacy"),
        ("transaction_domain", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_transaction_domain, noop_reverse),
    ]
