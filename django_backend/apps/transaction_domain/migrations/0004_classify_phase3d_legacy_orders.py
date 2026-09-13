"""Keep old orders LEGACY and stop before constraints on any unsafe V1 row."""

import re

from django.db import migrations, models


HASH_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
ORDER_STATUSES = {"CONFIRMED", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELLED"}
UNSAFE_KEYS = {
    "address", "authorization", "contact", "cookie", "credential",
    "customer_snapshot", "document_content", "email", "full_name", "password",
    "passwd", "phone", "quotation_snapshot", "secret", "session", "token",
}


def _unsafe_metadata(value, depth=0):
    if depth > 4:
        return True
    if value is None or isinstance(value, (bool, int, float)):
        return False
    if isinstance(value, str):
        return len(value) > 500
    if isinstance(value, list):
        return len(value) > 50 or any(_unsafe_metadata(item, depth + 1) for item in value)
    if isinstance(value, dict):
        if len(value) > 50:
            return True
        for key, item in value.items():
            if not isinstance(key, str):
                return True
            normalized = key.casefold()
            if any(fragment in normalized for fragment in UNSAFE_KEYS):
                return True
            if _unsafe_metadata(item, depth + 1):
                return True
        return False
    return True


def classify_and_validate(apps, schema_editor):
    order_model = apps.get_model("transaction_domain", "TransactionOrder")
    line_model = apps.get_model("transaction_domain", "TransactionOrderItem")
    progress_model = apps.get_model("transaction_domain", "OrderProgressEvent")
    audit_model = apps.get_model("transaction_domain", "AuditEvent")
    db_alias = schema_editor.connection.alias

    order_model.objects.using(db_alias).filter(
        source_quotation__isnull=True,
        source_rfq__isnull=True,
        workflow_status__isnull=True,
    ).update(data_contract="LEGACY")
    line_model.objects.using(db_alias).filter(
        order__data_contract="LEGACY"
    ).update(data_contract="LEGACY")

    v1_orders = order_model.objects.using(db_alias).filter(data_contract="MVP_V1")
    v1_lines = line_model.objects.using(db_alias).filter(data_contract="MVP_V1")
    violations = {
        "v1_order_required": v1_orders.filter(
            models.Q(source_quotation__isnull=True)
            | models.Q(source_rfq__isnull=True)
            | models.Q(workflow_status__isnull=True)
            | models.Q(currency__isnull=True)
            | models.Q(ordered_at__isnull=True)
            | models.Q(expected_delivery_date__isnull=True)
            | models.Q(idempotency_key__isnull=True)
            | models.Q(created_by__isnull=True)
            | models.Q(order_number="")
            | models.Q(request_hash="")
        ).count(),
        "v1_order_status": v1_orders.exclude(workflow_status__in=ORDER_STATUSES).count(),
        "v1_order_currency": v1_orders.exclude(currency__in=["VND", "USD"]).count(),
        "v1_order_money": v1_orders.filter(
            models.Q(subtotal__lt=0)
            | models.Q(discount_total__lt=0)
            | models.Q(tax_amount__lt=0)
            | models.Q(total_amount__lt=0)
            | models.Q(discount_total__gt=models.F("subtotal"))
        ).count(),
        "v1_order_total": v1_orders.exclude(
            total_amount=models.F("subtotal") - models.F("discount_total") + models.F("tax_amount")
        ).count(),
        "v1_order_progress": v1_orders.filter(
            models.Q(progress_percent__lt=0) | models.Q(progress_percent__gt=100)
        ).count(),
        "v1_order_hold_reason": v1_orders.filter(
            workflow_status="ON_HOLD", hold_reason=""
        ).count(),
        "v1_order_cancel_reason": v1_orders.filter(
            workflow_status="CANCELLED", cancel_reason=""
        ).count(),
        "v1_line_required": v1_lines.filter(
            models.Q(line_number__isnull=True)
            | models.Q(source_quotation_line__isnull=True)
            | models.Q(description_snapshot="")
            | models.Q(part_code_snapshot="")
            | models.Q(unit="")
        ).count(),
        "v1_line_values": v1_lines.filter(
            models.Q(quantity__lte=0)
            | models.Q(unit_price__lt=0)
            | models.Q(line_total__lt=0)
        ).count(),
        "progress_values": progress_model.objects.using(db_alias).filter(
            models.Q(progress_percent__lt=0)
            | models.Q(progress_percent__gt=100)
            | ~models.Q(to_status__in=ORDER_STATUSES)
        ).count(),
        "progress_reasons": progress_model.objects.using(db_alias).filter(
            to_status__in=["ON_HOLD", "CANCELLED"], reason=""
        ).count(),
        "audit_required": audit_model.objects.using(db_alias).filter(
            models.Q(actor_ref="")
            | models.Q(actor_display="")
            | models.Q(action="")
            | models.Q(entity_type="")
            | models.Q(entity_id="")
        ).count(),
    }

    for order in v1_orders.iterator():
        if not order.customer_snapshot or not order.quotation_snapshot:
            violations["v1_order_snapshots"] = violations.get("v1_order_snapshots", 0) + 1
        if order.idempotency_key and not HASH_PATTERN.fullmatch(order.request_hash or ""):
            violations["v1_order_request_hash"] = violations.get("v1_order_request_hash", 0) + 1
        if order.ordered_at and order.expected_delivery_date:
            if order.expected_delivery_date < order.ordered_at.date():
                violations["v1_order_delivery"] = violations.get("v1_order_delivery", 0) + 1
        if order.workflow_status == "COMPLETED" and order.completed_at_v1 is None:
            violations["v1_order_completion"] = violations.get("v1_order_completion", 0) + 1
        if order.source_quotation_id and order.source_rfq_id:
            if order.source_quotation.rfq_id != order.source_rfq_id:
                violations["v1_order_source_mismatch"] = violations.get("v1_order_source_mismatch", 0) + 1

    for line in v1_lines.iterator():
        if line.source_quotation_line_id and line.order.source_quotation_id:
            if line.source_quotation_line.quotation_id != line.order.source_quotation_id:
                violations["v1_line_source_mismatch"] = violations.get("v1_line_source_mismatch", 0) + 1

    for event in progress_model.objects.using(db_alias).iterator():
        if event.from_status and event.from_status not in ORDER_STATUSES:
            violations["progress_from_status"] = violations.get("progress_from_status", 0) + 1

    for event in audit_model.objects.using(db_alias).iterator():
        if event.actor_ref == "system":
            invalid_actor = event.actor_user_id is not None
        else:
            invalid_actor = event.actor_user_id is None or event.actor_ref != f"user:{event.actor_user_id}"
        if invalid_actor:
            violations["audit_actor_mismatch"] = violations.get("audit_actor_mismatch", 0) + 1
        if _unsafe_metadata(event.metadata):
            violations["audit_unsafe_metadata"] = violations.get("audit_unsafe_metadata", 0) + 1

    duplicate_queries = {
        "source_quotation_duplicates": v1_orders.exclude(source_quotation__isnull=True)
        .values("source_quotation_id").annotate(row_count=models.Count("id")).filter(row_count__gt=1),
        "idempotency_duplicates": order_model.objects.using(db_alias)
        .exclude(idempotency_key__isnull=True).values("idempotency_key")
        .annotate(row_count=models.Count("id")).filter(row_count__gt=1),
        "line_number_duplicates": line_model.objects.using(db_alias)
        .exclude(line_number__isnull=True).values("order_id", "line_number")
        .annotate(row_count=models.Count("id")).filter(row_count__gt=1),
        "source_line_duplicates": line_model.objects.using(db_alias)
        .exclude(source_quotation_line__isnull=True).values("source_quotation_line_id")
        .annotate(row_count=models.Count("id")).filter(row_count__gt=1),
    }
    violations.update({name: query.count() for name, query in duplicate_queries.items()})
    nonzero = {name: count for name, count in violations.items() if count}
    if nonzero:
        details = ", ".join(f"{name}={count}" for name, count in sorted(nonzero.items()))
        raise RuntimeError(f"BLOCKED_PHASE_3D_DATA_CONSTRAINT: {details}")


class Migration(migrations.Migration):
    dependencies = [("transaction_domain", "0003_phase3d_order_schema")]

    operations = [migrations.RunPython(classify_and_validate, migrations.RunPython.noop)]
