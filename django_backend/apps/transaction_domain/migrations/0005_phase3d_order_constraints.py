"""Activate named Phase 3D order, progress, and audit constraints."""

import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("foundation", "0009_seed_phase3d_rbac"),
        ("transaction_domain", "0004_classify_phase3d_legacy_orders"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="transactionorder",
            constraint=models.UniqueConstraint(
                condition=models.Q(("source_quotation__isnull", False)),
                fields=("source_quotation",),
                name="uq_order_source_quote",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorder",
            constraint=models.UniqueConstraint(
                condition=models.Q(("idempotency_key__isnull", False)),
                fields=("idempotency_key",),
                name="uq_order_idempotency_nonnull",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorder",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("data_contract", "MVP_V1"), _negated=True),
                    ("workflow_status__in", ["CONFIRMED", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELLED"]),
                    _connector="OR",
                ),
                name="ck_order_workflow_status",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorder",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("data_contract", "MVP_V1"), _negated=True),
                    models.Q(
                        ("source_quotation__isnull", False),
                        ("source_rfq__isnull", False),
                        ("workflow_status__isnull", False),
                        ("currency__isnull", False),
                        ("ordered_at__isnull", False),
                        ("expected_delivery_date__isnull", False),
                        ("idempotency_key__isnull", False),
                        ("created_by__isnull", False),
                        models.Q(("order_number", ""), _negated=True),
                        models.Q(("request_hash", ""), _negated=True),
                    ),
                    _connector="OR",
                ),
                name="ck_order_v1_required",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorder",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("data_contract", "MVP_V1"), _negated=True),
                    ("currency__in", ["VND", "USD"]),
                    _connector="OR",
                ),
                name="ck_order_currency",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorder",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("data_contract", "MVP_V1"), _negated=True),
                    models.Q(
                        ("subtotal__gte", 0),
                        ("discount_total__gte", 0),
                        ("tax_amount__gte", 0),
                        ("total_amount__gte", 0),
                    ),
                    _connector="OR",
                ),
                name="ck_order_money_nonneg",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorder",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("data_contract", "MVP_V1"), _negated=True),
                    ("discount_total__lte", models.F("subtotal")),
                    _connector="OR",
                ),
                name="ck_order_discount_bound",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorder",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("data_contract", "MVP_V1"), _negated=True),
                    (
                        "total_amount",
                        django.db.models.expressions.CombinedExpression(
                            django.db.models.expressions.CombinedExpression(
                                models.F("subtotal"), "-", models.F("discount_total")
                            ),
                            "+",
                            models.F("tax_amount"),
                        ),
                    ),
                    _connector="OR",
                ),
                name="ck_order_total_equation",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorder",
            constraint=models.CheckConstraint(
                condition=models.Q(("progress_percent__gte", 0), ("progress_percent__lte", 100)),
                name="ck_order_progress_range",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorder",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("data_contract", "MVP_V1"), ("workflow_status", "ON_HOLD"), _negated=True),
                    models.Q(("hold_reason", ""), _negated=True),
                    _connector="OR",
                ),
                name="ck_order_hold_reason",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorder",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("data_contract", "MVP_V1"), ("workflow_status", "CANCELLED"), _negated=True),
                    models.Q(("cancel_reason", ""), _negated=True),
                    _connector="OR",
                ),
                name="ck_order_cancel_reason",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorder",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("idempotency_key__isnull", True), ("request_hash", "")),
                    models.Q(("idempotency_key__isnull", False), models.Q(("request_hash", ""), _negated=True)),
                    _connector="OR",
                ),
                name="ck_order_idempotency_pair",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorder",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("idempotency_key__isnull", True),
                    ("request_hash__regex", "^[0-9a-fA-F]{64}$"),
                    _connector="OR",
                ),
                name="ck_order_request_hash",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorderitem",
            constraint=models.UniqueConstraint(
                condition=models.Q(("line_number__isnull", False)),
                fields=("order", "line_number"),
                name="uq_orderline_parent_number",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorderitem",
            constraint=models.UniqueConstraint(
                condition=models.Q(("source_quotation_line__isnull", False)),
                fields=("source_quotation_line",),
                name="uq_orderline_source_line",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorderitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("line_number__isnull", True), ("line_number__gt", 0), _connector="OR"),
                name="ck_orderline_number_pos",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorderitem",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("data_contract", "MVP_V1"), _negated=True),
                    ("quantity__gt", 0),
                    _connector="OR",
                ),
                name="ck_orderline_quantity_pos",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorderitem",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("data_contract", "MVP_V1"), _negated=True),
                    models.Q(("unit_price__gte", 0), ("line_total__gte", 0)),
                    _connector="OR",
                ),
                name="ck_orderline_money_nonneg",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorderitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("unit", ""), ("unit__in", ["PCS", "KG", "M", "MM"]), _connector="OR"),
                name="ck_orderline_unit",
            ),
        ),
        migrations.AddConstraint(
            model_name="transactionorderitem",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("data_contract", "MVP_V1"), _negated=True),
                    models.Q(
                        ("line_number__isnull", False),
                        ("source_quotation_line__isnull", False),
                        models.Q(("description_snapshot", ""), _negated=True),
                        models.Q(("part_code_snapshot", ""), _negated=True),
                        models.Q(("unit", ""), _negated=True),
                    ),
                    _connector="OR",
                ),
                name="ck_orderline_v1_required",
            ),
        ),
        migrations.AddConstraint(
            model_name="orderprogressevent",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(
                        ("from_status", ""),
                        ("from_status__in", ["CONFIRMED", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELLED"]),
                        _connector="OR",
                    ),
                    ("to_status__in", ["CONFIRMED", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELLED"]),
                ),
                name="ck_progress_statuses",
            ),
        ),
        migrations.AddConstraint(
            model_name="orderprogressevent",
            constraint=models.CheckConstraint(
                condition=models.Q(("progress_percent__gte", 0), ("progress_percent__lte", 100)),
                name="ck_progress_percent_range",
            ),
        ),
        migrations.AddConstraint(
            model_name="orderprogressevent",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("to_status__in", ["ON_HOLD", "CANCELLED"]), _negated=True),
                    models.Q(("reason", ""), _negated=True),
                    _connector="OR",
                ),
                name="ck_progress_reason",
            ),
        ),
        migrations.AddConstraint(
            model_name="auditevent",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("actor_ref", ""), _negated=True),
                    models.Q(("actor_display", ""), _negated=True),
                ),
                name="ck_audit_actor_ref",
            ),
        ),
        migrations.AddConstraint(
            model_name="auditevent",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("action", ""), _negated=True),
                    models.Q(("entity_type", ""), _negated=True),
                    models.Q(("entity_id", ""), _negated=True),
                ),
                name="ck_audit_required",
            ),
        ),
    ]
