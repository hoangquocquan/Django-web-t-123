"""Phase 3C quotation invariants without API or command-layer coupling."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.utils import timezone

from apps.business_core.business_numbers import allocate_business_number

from .models import (
    QUOTATION_APPROVAL_DECISION_CHOICES,
    QUOTATION_CURRENCY_CHOICES,
    QUOTATION_CUSTOMER_DECISION_CHOICES,
    SalesQuotation,
    SalesQuotationApprovalDecision,
    SalesQuotationCustomerDecision,
    SalesQuotationLine,
    SalesRfq,
    SalesRfqLine,
)


MAX_REVISION_ALLOCATION_ATTEMPTS = 3
STORAGE_QUANTUM = Decimal("0.0001")
SETTLEMENT_QUANTA = {"USD": Decimal("0.01"), "VND": Decimal("1")}
HASH_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


def decimal_value(value, field_name):
    """Parse a finite Decimal without accepting float arithmetic as authority."""
    if isinstance(value, float):
        raise ValidationError({field_name: "Float values are not accepted."})
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError({field_name: "A finite decimal value is required."}) from exc
    if not parsed.is_finite():
        raise ValidationError({field_name: "A finite decimal value is required."})
    return parsed


def quantize_money(value, currency):
    """Apply the Phase 3A settlement quantum and retain four storage decimals."""
    normalized_currency = str(currency).upper()
    if normalized_currency not in dict(QUOTATION_CURRENCY_CHOICES):
        raise ValidationError({"currency": "Only VND and USD are supported."})
    parsed = decimal_value(value, "money")
    settled = parsed.quantize(SETTLEMENT_QUANTA[normalized_currency], rounding=ROUND_HALF_UP)
    return settled.quantize(STORAGE_QUANTUM)


def calculate_line_amounts(*, quantity, unit_price, discount, currency):
    """Calculate one quotation line using Decimal and currency rounding."""
    parsed_quantity = decimal_value(quantity, "quantity").quantize(
        STORAGE_QUANTUM, rounding=ROUND_HALF_UP
    )
    parsed_unit_price = decimal_value(unit_price, "unit_price").quantize(
        STORAGE_QUANTUM, rounding=ROUND_HALF_UP
    )
    if parsed_quantity <= 0:
        raise ValidationError({"quantity": "Quantity must be positive."})
    if parsed_unit_price <= 0:
        raise ValidationError({"unit_price": "Unit price must be positive."})
    line_subtotal = quantize_money(parsed_quantity * parsed_unit_price, currency)
    line_discount = quantize_money(discount, currency)
    if line_discount < 0 or line_discount > line_subtotal:
        raise ValidationError({"discount": "Discount must be between zero and line subtotal."})
    line_total = quantize_money(line_subtotal - line_discount, currency)
    return {
        "quantity": parsed_quantity,
        "unit_price": parsed_unit_price,
        "discount": line_discount,
        "line_subtotal": line_subtotal,
        "line_total": line_total,
    }


def calculate_header_amounts(*, line_subtotals, discount_total, tax_amount, currency):
    """Calculate canonical header totals from already-quantized line subtotals."""
    subtotal = sum((decimal_value(value, "line_subtotal") for value in line_subtotals), Decimal("0"))
    subtotal = subtotal.quantize(STORAGE_QUANTUM)
    discount = quantize_money(discount_total, currency)
    tax = quantize_money(tax_amount, currency)
    if subtotal < 0:
        raise ValidationError({"subtotal": "Subtotal cannot be negative."})
    if discount < 0 or discount > subtotal:
        raise ValidationError({"discount_total": "Discount must be between zero and subtotal."})
    if tax < 0:
        raise ValidationError({"tax_amount": "Tax cannot be negative."})
    return {
        "subtotal": subtotal,
        "discount_total": discount,
        "tax_amount": tax,
        "total": quantize_money(subtotal - discount + tax, currency),
    }


def _customer_snapshot(customer):
    return {
        "id": customer.pk,
        "customer_code": customer.customer_code,
        "company_name": customer.company_name,
        "contact_name": customer.contact_name,
        "email": customer.email,
        "phone": customer.phone,
    }


def _rfq_snapshot(rfq):
    return {
        "id": rfq.pk,
        "rfq_number": rfq.rfq_number,
        "project_name": rfq.project_name,
        "quote_due_at": rfq.quote_due_at.isoformat(),
        "required_delivery_date": rfq.required_delivery_date.isoformat(),
    }


def _prepare_line(source_line, pricing, currency, line_number):
    if source_line.part_id is None or not source_line.part.part_code:
        raise ValidationError(
            {"source_rfq_line": "A canonical Part code is required for a quotation snapshot."}
        )
    amounts = calculate_line_amounts(
        quantity=source_line.quantity,
        unit_price=pricing["unit_price"],
        discount=pricing.get("discount", "0"),
        currency=currency,
    )
    material_snapshot = ""
    if source_line.material_id:
        material_snapshot = " - ".join(
            value
            for value in (source_line.material.material_code, source_line.material.name)
            if value
        )
    return {
        "line_number": line_number,
        "source_rfq_line": source_line,
        "product": source_line.part,
        "description": source_line.description,
        "part_code_snapshot": source_line.part.part_code,
        "material_snapshot": material_snapshot,
        "unit": source_line.unit,
        **amounts,
    }


def _validate_create_input(*, currency, valid_from, valid_until, idempotency_key, request_hash, pricing_lines):
    normalized_currency = str(currency).upper()
    if normalized_currency not in dict(QUOTATION_CURRENCY_CHOICES):
        raise ValidationError({"currency": "Only VND and USD are supported."})
    if not valid_from or not valid_until or valid_until < valid_from:
        raise ValidationError({"valid_until": "Validity end must not precede validity start."})
    if not idempotency_key:
        raise ValidationError({"idempotency_key": "Idempotency key is required."})
    if not HASH_PATTERN.fullmatch(str(request_hash)):
        raise ValidationError({"request_hash": "Request hash must be 64 hexadecimal characters."})
    if not pricing_lines:
        raise ValidationError({"lines": "At least one quotation line is required."})
    source_ids = [item.get("source_rfq_line_id") for item in pricing_lines]
    if any(source_id is None for source_id in source_ids) or len(set(source_ids)) != len(source_ids):
        raise ValidationError({"lines": "Source RFQ lines must be present and unique."})
    return normalized_currency


def _create_quotation_revision_once(
    *,
    rfq_id,
    created_by_id,
    currency,
    valid_from,
    valid_until,
    pricing_lines,
    discount_total,
    tax_amount,
    terms,
    idempotency_key,
    request_hash,
):
    with transaction.atomic():
        rfq = (
            SalesRfq.objects.select_for_update()
            .select_related("customer")
            .get(pk=rfq_id)
        )
        existing = SalesQuotation.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            if existing.request_hash == request_hash and existing.rfq_id == rfq_id:
                return existing
            raise ValidationError({"idempotency_key": "Key was already used for another request."})
        if rfq.status != "READY_TO_QUOTE":
            raise ValidationError({"rfq": "RFQ must be READY_TO_QUOTE."})

        latest = (
            SalesQuotation.objects.filter(
                rfq=rfq,
                data_contract="MVP_V1",
                revision__isnull=False,
            )
            .order_by("-revision")
            .first()
        )
        if latest and latest.workflow_status != "REJECTED":
            raise ValidationError({"rfq": "A new revision requires the latest revision to be REJECTED."})

        if not rfq.quotation_family_number:
            rfq.quotation_family_number = allocate_business_number("QT")
            rfq.save(update_fields=["quotation_family_number", "updated_at"])

        revision_max = SalesQuotation.objects.filter(rfq=rfq).aggregate(value=Max("revision"))["value"]
        revision = 0 if revision_max is None else revision_max + 1
        if latest:
            SalesQuotation.objects.filter(pk=latest.pk).update(workflow_status="SUPERSEDED")

        requested_ids = [item["source_rfq_line_id"] for item in pricing_lines]
        source_lines = {
            line.pk: line
            for line in SalesRfqLine.objects.select_related("part", "material").filter(
                rfq=rfq, pk__in=requested_ids
            )
        }
        if len(source_lines) != len(requested_ids):
            raise ValidationError({"lines": "Every source line must belong to the RFQ."})
        prepared_lines = [
            _prepare_line(source_lines[item["source_rfq_line_id"]], item, currency, index)
            for index, item in enumerate(pricing_lines, start=1)
        ]
        header = calculate_header_amounts(
            line_subtotals=[item["line_subtotal"] for item in prepared_lines],
            discount_total=discount_total,
            tax_amount=tax_amount,
            currency=currency,
        )
        quotation = SalesQuotation.objects.create(
            data_contract="MVP_V1",
            rfq=rfq,
            customer=rfq.customer,
            quotation_number=f"{rfq.quotation_family_number}-R{revision}",
            revision=revision,
            workflow_status="DRAFT",
            currency=currency,
            valid_from=valid_from,
            valid_until=valid_until,
            terms=terms,
            customer_snapshot=_customer_snapshot(rfq.customer),
            rfq_snapshot=_rfq_snapshot(rfq),
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            created_by_id=created_by_id,
            updated_by_id=created_by_id,
            **header,
        )
        for item in prepared_lines:
            SalesQuotationLine.objects.create(
                quotation=quotation,
                data_contract="MVP_V1",
                **item,
            )
        return quotation


def create_quotation_revision(
    *,
    rfq_id,
    created_by_id,
    currency,
    valid_from,
    valid_until,
    pricing_lines,
    discount_total="0",
    tax_amount="0",
    terms="",
    idempotency_key,
    request_hash,
    max_attempts=MAX_REVISION_ALLOCATION_ATTEMPTS,
):
    """Create one revision with family/revision allocation in a single transaction."""
    currency = _validate_create_input(
        currency=currency,
        valid_from=valid_from,
        valid_until=valid_until,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        pricing_lines=pricing_lines,
    )
    attempts = min(max(int(max_attempts), 1), MAX_REVISION_ALLOCATION_ATTEMPTS)
    last_error = None
    for _attempt in range(attempts):
        try:
            return _create_quotation_revision_once(
                rfq_id=rfq_id,
                created_by_id=created_by_id,
                currency=currency,
                valid_from=valid_from,
                valid_until=valid_until,
                pricing_lines=pricing_lines,
                discount_total=discount_total,
                tax_amount=tax_amount,
                terms=terms,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
            )
        except IntegrityError as exc:
            last_error = exc
    raise last_error


def update_draft_quotation(
    *,
    quotation_id,
    actor_id,
    currency=None,
    valid_from=None,
    valid_until=None,
    pricing_lines=None,
    discount_total=None,
    tax_amount=None,
    terms=None,
):
    """Replace editable draft pricing and recalculate authoritative amounts."""
    with transaction.atomic():
        quotation = (
            SalesQuotation.objects.select_for_update(of=("self",))
            .select_related("rfq")
            .get(pk=quotation_id)
        )
        if quotation.data_contract != "MVP_V1" or quotation.workflow_status != "DRAFT":
            raise ValidationError({"quotation": "Only a canonical DRAFT can be edited."})

        normalized_currency = str(currency or quotation.currency).upper()
        next_valid_from = valid_from or quotation.valid_from
        next_valid_until = valid_until or quotation.valid_until
        if normalized_currency not in dict(QUOTATION_CURRENCY_CHOICES):
            raise ValidationError({"currency": "Only VND and USD are supported."})
        if not next_valid_from or not next_valid_until or next_valid_until < next_valid_from:
            raise ValidationError({"valid_until": "Validity end must not precede validity start."})

        if pricing_lines is not None:
            if not pricing_lines:
                raise ValidationError({"lines": "At least one quotation line is required."})
            source_ids = [item.get("source_rfq_line_id") for item in pricing_lines]
            if any(item is None for item in source_ids) or len(set(source_ids)) != len(source_ids):
                raise ValidationError({"lines": "Source RFQ lines must be present and unique."})
            source_lines = {
                line.pk: line
                for line in SalesRfqLine.objects.select_related("part", "material").filter(
                    rfq_id=quotation.rfq_id,
                    pk__in=source_ids,
                )
            }
            if len(source_lines) != len(source_ids):
                raise ValidationError({"lines": "Every source line must belong to the RFQ."})
            prepared_lines = [
                _prepare_line(
                    source_lines[item["source_rfq_line_id"]],
                    item,
                    normalized_currency,
                    index,
                )
                for index, item in enumerate(pricing_lines, start=1)
            ]
            quotation.lines.all().delete()
            for item in prepared_lines:
                SalesQuotationLine.objects.create(
                    quotation=quotation,
                    data_contract="MVP_V1",
                    **item,
                )
            lines = list(quotation.lines.order_by("line_number", "id"))
        else:
            lines = list(quotation.lines.select_for_update().order_by("line_number", "id"))
            if not lines:
                raise ValidationError({"lines": "At least one quotation line is required."})
            for line in lines:
                amounts = calculate_line_amounts(
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    discount=line.discount,
                    currency=normalized_currency,
                )
                for field, value in amounts.items():
                    setattr(line, field, value)
                line.save(update_fields=list(amounts))

        header = calculate_header_amounts(
            line_subtotals=[line.line_subtotal for line in lines],
            discount_total=(
                quotation.discount_total if discount_total is None else discount_total
            ),
            tax_amount=quotation.tax_amount if tax_amount is None else tax_amount,
            currency=normalized_currency,
        )
        quotation.currency = normalized_currency
        quotation.valid_from = next_valid_from
        quotation.valid_until = next_valid_until
        if terms is not None:
            quotation.terms = str(terms)
        quotation.updated_by_id = actor_id
        for field, value in header.items():
            setattr(quotation, field, value)
        quotation.save(
            update_fields=[
                "currency",
                "valid_from",
                "valid_until",
                "terms",
                "updated_by",
                *header,
                "updated_at",
            ]
        )
        return quotation


def archive_draft_quotation(*, quotation_id, actor_id):
    """Retire an eligible draft while preserving its revision history."""
    with transaction.atomic():
        quotation = SalesQuotation.objects.select_for_update().get(pk=quotation_id)
        if quotation.data_contract != "MVP_V1" or quotation.workflow_status != "DRAFT":
            raise ValidationError({"quotation": "Only a canonical DRAFT can be archived."})
        quotation.workflow_status = "SUPERSEDED"
        quotation.updated_by_id = actor_id
        quotation.save(update_fields=["workflow_status", "updated_by", "updated_at"])
        return quotation


def submit_quotation(quotation_id, actor_id):
    """Recalculate authoritative totals and lock a draft for approval."""
    with transaction.atomic():
        quotation = SalesQuotation.objects.select_for_update().get(pk=quotation_id)
        if quotation.data_contract != "MVP_V1" or quotation.workflow_status != "DRAFT":
            raise ValidationError({"quotation": "Only a canonical DRAFT can be submitted."})
        lines = list(quotation.lines.order_by("line_number"))
        if not lines:
            raise ValidationError({"lines": "At least one quotation line is required."})
        for line in lines:
            expected = calculate_line_amounts(
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount=line.discount,
                currency=quotation.currency,
            )
            if any(getattr(line, field) != value for field, value in expected.items()):
                raise ValidationError({"lines": "Stored line amounts do not match backend calculation."})
        expected_header = calculate_header_amounts(
            line_subtotals=[line.line_subtotal for line in lines],
            discount_total=quotation.discount_total,
            tax_amount=quotation.tax_amount,
            currency=quotation.currency,
        )
        if any(getattr(quotation, field) != value for field, value in expected_header.items()):
            raise ValidationError({"total": "Stored header amounts do not match backend calculation."})
        if not quotation.customer_snapshot or not quotation.rfq_snapshot:
            raise ValidationError({"snapshots": "Customer and RFQ snapshots are required."})
        quotation.workflow_status = "PENDING_APPROVAL"
        quotation.updated_by_id = actor_id
        quotation.save(update_fields=["workflow_status", "updated_by", "updated_at"])
        return quotation


def record_quotation_approval(*, quotation_id, reviewer_id, decision, reason="", notes=""):
    """Record an immutable maker-checker decision and transition atomically."""
    decision = str(decision).upper()
    if decision not in dict(QUOTATION_APPROVAL_DECISION_CHOICES):
        raise ValidationError({"decision": "Decision must be APPROVED or REJECTED."})
    reason = str(reason).strip()
    if decision == "REJECTED" and not reason:
        raise ValidationError({"reason": "Rejection reason is required."})
    rfq_id = SalesQuotation.objects.only("rfq_id").get(pk=quotation_id).rfq_id
    with transaction.atomic():
        SalesRfq.objects.select_for_update().get(pk=rfq_id)
        quotation = SalesQuotation.objects.select_for_update().get(pk=quotation_id)
        if quotation.workflow_status != "PENDING_APPROVAL":
            raise ValidationError({"quotation": "Quotation is not pending approval."})
        if quotation.created_by_id == reviewer_id:
            raise ValidationError({"reviewer": "Quotation creator cannot decide it."})
        if decision == "APPROVED":
            effective = SalesQuotation.objects.select_for_update().filter(
                rfq_id=quotation.rfq_id,
                data_contract="MVP_V1",
                workflow_status__in=["APPROVED", "SENT", "ACCEPTED"],
            ).exclude(pk=quotation.pk)
            if effective.filter(workflow_status="ACCEPTED").exists():
                raise ValidationError({"quotation": "An accepted revision cannot be superseded."})
            effective.update(workflow_status="SUPERSEDED")
        approval = SalesQuotationApprovalDecision.objects.create(
            quotation=quotation,
            reviewer_id=reviewer_id,
            decision=decision,
            reason=reason,
            notes=notes,
        )
        quotation.workflow_status = decision
        quotation.save(update_fields=["workflow_status", "updated_at"])
        return approval


def mark_quotation_sent(*, quotation_id, actor_id, sent_to, evidence, sent_at=None):
    """Record send evidence without modifying the commercial snapshot."""
    sent_to = str(sent_to).strip()
    evidence = str(evidence).strip()
    if not sent_to or not evidence:
        raise ValidationError({"sent_evidence": "Recipient and send evidence are required."})
    instant = sent_at or timezone.now()
    with transaction.atomic():
        quotation = SalesQuotation.objects.select_for_update().get(pk=quotation_id)
        if quotation.workflow_status != "APPROVED":
            raise ValidationError({"quotation": "Only an approved quotation can be sent."})
        decision_date = timezone.localdate(instant)
        if decision_date < quotation.valid_from or decision_date > quotation.valid_until:
            raise ValidationError({"valid_until": "Quotation is outside its validity window."})
        quotation.workflow_status = "SENT"
        quotation.sent_at = instant
        quotation.sent_to = sent_to
        quotation.sent_evidence = evidence
        quotation.updated_by_id = actor_id
        quotation.save(
            update_fields=[
                "workflow_status",
                "sent_at",
                "sent_to",
                "sent_evidence",
                "updated_by",
                "updated_at",
            ]
        )
        return quotation


def record_customer_decision(
    *,
    quotation_id,
    recorded_by_id,
    decision,
    contact_snapshot,
    evidence,
    reason="",
    decided_at=None,
):
    """Record one immutable customer decision against an eligible sent revision."""
    decision = str(decision).upper()
    if decision not in dict(QUOTATION_CUSTOMER_DECISION_CHOICES):
        raise ValidationError({"decision": "Decision must be ACCEPTED or DECLINED."})
    contact_snapshot = str(contact_snapshot).strip()
    evidence = str(evidence).strip()
    reason = str(reason).strip()
    if not contact_snapshot or not evidence:
        raise ValidationError({"evidence": "Customer contact and evidence are required."})
    if decision == "DECLINED" and not reason:
        raise ValidationError({"reason": "Decline reason is required."})
    instant = decided_at or timezone.now()
    with transaction.atomic():
        quotation = SalesQuotation.objects.select_for_update().get(pk=quotation_id)
        if quotation.workflow_status != "SENT":
            raise ValidationError({"quotation": "Customer decision requires a sent quotation."})
        if decision == "ACCEPTED" and timezone.localdate(instant) > quotation.valid_until:
            raise ValidationError({"valid_until": "An expired quotation cannot be accepted."})
        customer_decision = SalesQuotationCustomerDecision.objects.create(
            quotation=quotation,
            recorded_by_id=recorded_by_id,
            decision=decision,
            contact_snapshot=contact_snapshot,
            evidence=evidence,
            reason=reason,
            decided_at=instant,
        )
        quotation.workflow_status = decision
        quotation.save(update_fields=["workflow_status", "updated_at"])
        return customer_decision
