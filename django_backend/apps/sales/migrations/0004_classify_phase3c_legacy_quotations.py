"""Classify ambiguous existing quotations as LEGACY and preflight V1 rows."""

from django.db import migrations, models


def classify_and_validate(apps, schema_editor):
    quotation_model = apps.get_model("sales", "SalesQuotation")
    line_model = apps.get_model("sales", "SalesQuotationLine")
    approval_model = apps.get_model("sales", "SalesQuotationApprovalDecision")
    customer_decision_model = apps.get_model("sales", "SalesQuotationCustomerDecision")
    db_alias = schema_editor.connection.alias

    ambiguous_quotes = quotation_model.objects.using(db_alias).filter(
        rfq__isnull=True,
        revision__isnull=True,
        workflow_status__isnull=True,
    )
    ambiguous_quotes.update(data_contract="LEGACY")
    line_model.objects.using(db_alias).filter(
        quotation__data_contract="LEGACY"
    ).update(data_contract="LEGACY")

    v1_quotes = quotation_model.objects.using(db_alias).filter(data_contract="MVP_V1")
    v1_lines = line_model.objects.using(db_alias).filter(data_contract="MVP_V1")
    violations = {
        "v1_quote_required": v1_quotes.filter(
            models.Q(rfq__isnull=True)
            | models.Q(customer__isnull=True)
            | models.Q(revision__isnull=True)
            | models.Q(workflow_status__isnull=True)
            | models.Q(currency__isnull=True)
            | models.Q(valid_from__isnull=True)
            | models.Q(valid_until__isnull=True)
            | models.Q(created_by__isnull=True)
            | models.Q(idempotency_key__isnull=True)
            | models.Q(quotation_number="")
            | models.Q(request_hash="")
        ).count(),
        "v1_quote_status": v1_quotes.exclude(
            workflow_status__in=[
                "DRAFT",
                "PENDING_APPROVAL",
                "APPROVED",
                "REJECTED",
                "SENT",
                "ACCEPTED",
                "DECLINED",
                "EXPIRED",
                "SUPERSEDED",
            ]
        ).count(),
        "v1_quote_currency": v1_quotes.exclude(currency__in=["VND", "USD"]).count(),
        "v1_quote_validity": v1_quotes.filter(valid_until__lt=models.F("valid_from")).count(),
        "v1_quote_money": v1_quotes.filter(
            models.Q(subtotal__lt=0)
            | models.Q(discount_total__lt=0)
            | models.Q(tax_amount__lt=0)
            | models.Q(total__lt=0)
            | models.Q(discount_total__gt=models.F("subtotal"))
        ).count(),
        "v1_quote_total": v1_quotes.exclude(
            total=models.F("subtotal") - models.F("discount_total") + models.F("tax_amount")
        ).count(),
        "v1_line_required": v1_lines.filter(
            models.Q(line_number__isnull=True)
            | models.Q(source_rfq_line__isnull=True)
            | models.Q(description="")
            | models.Q(part_code_snapshot="")
            | models.Q(unit="")
        ).count(),
        "v1_line_money": v1_lines.filter(
            models.Q(quantity__lte=0)
            | models.Q(unit_price__lte=0)
            | models.Q(discount__lt=0)
            | models.Q(line_subtotal__lt=0)
            | models.Q(line_total__lt=0)
            | models.Q(discount__gt=models.F("line_subtotal"))
        ).count(),
        "v1_line_total": v1_lines.exclude(
            line_total=models.F("line_subtotal") - models.F("discount")
        ).count(),
        "maker_checker": approval_model.objects.using(db_alias).filter(
            reviewer_id=models.F("quotation__created_by_id")
        ).count(),
        "approval_without_reason": approval_model.objects.using(db_alias).filter(
            decision="REJECTED", reason=""
        ).count(),
        "customer_without_evidence": customer_decision_model.objects.using(db_alias).filter(
            models.Q(contact_snapshot="") | models.Q(evidence="")
        ).count(),
        "customer_decline_without_reason": customer_decision_model.objects.using(db_alias).filter(
            decision="DECLINED", reason=""
        ).count(),
    }

    duplicate_queries = {
        "rfq_revision_duplicates": quotation_model.objects.using(db_alias)
        .exclude(rfq__isnull=True)
        .exclude(revision__isnull=True)
        .values("rfq_id", "revision")
        .annotate(row_count=models.Count("id"))
        .filter(row_count__gt=1),
        "idempotency_duplicates": quotation_model.objects.using(db_alias)
        .exclude(idempotency_key__isnull=True)
        .values("idempotency_key")
        .annotate(row_count=models.Count("id"))
        .filter(row_count__gt=1),
        "line_number_duplicates": line_model.objects.using(db_alias)
        .exclude(line_number__isnull=True)
        .values("quotation_id", "line_number")
        .annotate(row_count=models.Count("id"))
        .filter(row_count__gt=1),
    }
    violations.update({name: query.count() for name, query in duplicate_queries.items()})
    nonzero = {name: count for name, count in violations.items() if count}
    if nonzero:
        details = ", ".join(f"{name}={count}" for name, count in sorted(nonzero.items()))
        raise RuntimeError(f"BLOCKED_PHASE_3C_DATA_CONSTRAINT: {details}")


class Migration(migrations.Migration):
    dependencies = [("sales", "0003_phase3c_quotation_schema")]

    operations = [
        migrations.RunPython(classify_and_validate, migrations.RunPython.noop),
    ]
