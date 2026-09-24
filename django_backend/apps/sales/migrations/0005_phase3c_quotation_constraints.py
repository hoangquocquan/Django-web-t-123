"""Activate named Phase 3C quotation constraints after legacy classification."""

import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("sales", "0004_classify_phase3c_legacy_quotations")]

    operations = [
        migrations.AddConstraint(
            model_name="salesquotation",
            constraint=models.UniqueConstraint(condition=models.Q(("revision__isnull", False), ("rfq__isnull", False)), fields=("rfq", "revision"), name="uq_quote_rfq_revision"),
        ),
        migrations.AddConstraint(
            model_name="salesquotation",
            constraint=models.UniqueConstraint(condition=models.Q(("data_contract", "MVP_V1"), ("workflow_status__in", ["APPROVED", "SENT", "ACCEPTED"])), fields=("rfq",), name="uq_quote_effective_rfq"),
        ),
        migrations.AddConstraint(
            model_name="salesquotation",
            constraint=models.UniqueConstraint(condition=models.Q(("idempotency_key__isnull", False)), fields=("idempotency_key",), name="uq_quote_idempotency_nonnull"),
        ),
        migrations.AddConstraint(
            model_name="salesquotation",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("data_contract", "MVP_V1"), _negated=True), ("workflow_status__in", ["DRAFT", "PENDING_APPROVAL", "APPROVED", "REJECTED", "SENT", "ACCEPTED", "DECLINED", "EXPIRED", "SUPERSEDED"]), _connector="OR"), name="ck_quote_workflow_status"),
        ),
        migrations.AddConstraint(
            model_name="salesquotation",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("data_contract", "MVP_V1"), _negated=True), models.Q(("rfq__isnull", False), ("customer__isnull", False), ("revision__isnull", False), ("workflow_status__isnull", False), ("currency__isnull", False), ("valid_from__isnull", False), ("valid_until__isnull", False), ("created_by__isnull", False), ("idempotency_key__isnull", False), models.Q(("quotation_number", ""), _negated=True), models.Q(("request_hash", ""), _negated=True)), _connector="OR"), name="ck_quote_v1_required"),
        ),
        migrations.AddConstraint(
            model_name="salesquotation",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("data_contract", "MVP_V1"), _negated=True), ("currency__in", ["VND", "USD"]), _connector="OR"), name="ck_quote_currency"),
        ),
        migrations.AddConstraint(
            model_name="salesquotation",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("data_contract", "MVP_V1"), _negated=True), ("valid_until__gte", models.F("valid_from")), _connector="OR"), name="ck_quote_validity"),
        ),
        migrations.AddConstraint(
            model_name="salesquotation",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("data_contract", "MVP_V1"), _negated=True), models.Q(("subtotal__gte", 0), ("discount_total__gte", 0), ("tax_amount__gte", 0), ("total__gte", 0)), _connector="OR"), name="ck_quote_money_nonneg"),
        ),
        migrations.AddConstraint(
            model_name="salesquotation",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("data_contract", "MVP_V1"), _negated=True), ("discount_total__lte", models.F("subtotal")), _connector="OR"), name="ck_quote_discount_bound"),
        ),
        migrations.AddConstraint(
            model_name="salesquotation",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("data_contract", "MVP_V1"), _negated=True), ("total", django.db.models.expressions.CombinedExpression(django.db.models.expressions.CombinedExpression(models.F("subtotal"), "-", models.F("discount_total")), "+", models.F("tax_amount"))), _connector="OR"), name="ck_quote_total_equation"),
        ),
        migrations.AddConstraint(
            model_name="salesquotation",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("idempotency_key__isnull", True), ("request_hash", "")), models.Q(("idempotency_key__isnull", False), models.Q(("request_hash", ""), _negated=True)), _connector="OR"), name="ck_quote_idempotency_pair"),
        ),
        migrations.AddConstraint(
            model_name="salesquotation",
            constraint=models.CheckConstraint(condition=models.Q(("idempotency_key__isnull", True), ("request_hash__regex", "^[0-9a-fA-F]{64}$"), _connector="OR"), name="ck_quote_request_hash"),
        ),
        migrations.AddConstraint(
            model_name="salesquotationline",
            constraint=models.UniqueConstraint(condition=models.Q(("line_number__isnull", False)), fields=("quotation", "line_number"), name="uq_quoteline_parent_number"),
        ),
        migrations.AddConstraint(
            model_name="salesquotationline",
            constraint=models.CheckConstraint(condition=models.Q(("line_number__isnull", True), ("line_number__gt", 0), _connector="OR"), name="ck_quoteline_number_pos"),
        ),
        migrations.AddConstraint(
            model_name="salesquotationline",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("data_contract", "MVP_V1"), _negated=True), ("quantity__gt", 0), _connector="OR"), name="ck_quoteline_quantity_pos"),
        ),
        migrations.AddConstraint(
            model_name="salesquotationline",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("data_contract", "MVP_V1"), _negated=True), ("unit_price__gt", 0), _connector="OR"), name="ck_quoteline_price_pos"),
        ),
        migrations.AddConstraint(
            model_name="salesquotationline",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("data_contract", "MVP_V1"), _negated=True), models.Q(("discount__gte", 0), ("line_subtotal__gte", 0), ("line_total__gte", 0)), _connector="OR"), name="ck_quoteline_money_nonneg"),
        ),
        migrations.AddConstraint(
            model_name="salesquotationline",
            constraint=models.CheckConstraint(condition=models.Q(("unit", ""), ("unit__in", ["PCS", "KG", "M", "MM"]), _connector="OR"), name="ck_quoteline_unit"),
        ),
        migrations.AddConstraint(
            model_name="salesquotationline",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("data_contract", "MVP_V1"), _negated=True), models.Q(("line_number__isnull", False), ("source_rfq_line__isnull", False), models.Q(("description", ""), _negated=True), models.Q(("part_code_snapshot", ""), _negated=True), models.Q(("unit", ""), _negated=True)), _connector="OR"), name="ck_quoteline_v1_required"),
        ),
        migrations.AddConstraint(
            model_name="salesquotationline",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("data_contract", "MVP_V1"), _negated=True), ("discount__lte", models.F("line_subtotal")), _connector="OR"), name="ck_quoteline_discount_bound"),
        ),
        migrations.AddConstraint(
            model_name="salesquotationline",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("data_contract", "MVP_V1"), _negated=True), ("line_total", django.db.models.expressions.CombinedExpression(models.F("line_subtotal"), "-", models.F("discount"))), _connector="OR"), name="ck_quoteline_total_equation"),
        ),
        migrations.AddConstraint(
            model_name="salesquotationapprovaldecision",
            constraint=models.UniqueConstraint(fields=("quotation",), name="uq_quote_approval_decision"),
        ),
        migrations.AddConstraint(
            model_name="salesquotationapprovaldecision",
            constraint=models.CheckConstraint(condition=models.Q(("decision__in", ["APPROVED", "REJECTED"])), name="ck_quoteapproval_decision"),
        ),
        migrations.AddConstraint(
            model_name="salesquotationapprovaldecision",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("decision", "REJECTED"), _negated=True), models.Q(("reason", ""), _negated=True), _connector="OR"), name="ck_quoteapproval_reason"),
        ),
        migrations.AddConstraint(
            model_name="salesquotationcustomerdecision",
            constraint=models.UniqueConstraint(fields=("quotation",), name="uq_quote_customer_decision"),
        ),
        migrations.AddConstraint(
            model_name="salesquotationcustomerdecision",
            constraint=models.CheckConstraint(condition=models.Q(("decision__in", ["ACCEPTED", "DECLINED"])), name="ck_quotecustomer_decision"),
        ),
        migrations.AddConstraint(
            model_name="salesquotationcustomerdecision",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("contact_snapshot", ""), _negated=True), models.Q(("evidence", ""), _negated=True)), name="ck_quotecustomer_required"),
        ),
        migrations.AddConstraint(
            model_name="salesquotationcustomerdecision",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("decision", "DECLINED"), _negated=True), models.Q(("reason", ""), _negated=True), _connector="OR"), name="ck_quotecustomer_reason"),
        ),
    ]
