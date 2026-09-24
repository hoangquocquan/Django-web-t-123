"""Atomic Phase 3D quotation conversion, order progress, audit, and RBAC."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, InvalidOperation
import re
import uuid

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.business_core.business_numbers import allocate_business_number
from apps.foundation.models import FoundationUser
from apps.foundation.services import FoundationPermissionService
from apps.sales.models import (
    SalesQuotation,
    SalesQuotationCustomerDecision,
    SalesQuotationLine,
    SalesRfq,
)
from apps.sales.quotation_domain import calculate_header_amounts, calculate_line_amounts

from .models import AuditEvent, OrderProgressEvent, TransactionOrder, TransactionOrderItem


HASH_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
CONVERSION_ROLES = {"Admin", "Sales"}
PROGRESS_ROLES = {"Admin", "Manager"}
ALLOWED_TRANSITIONS = {
    "CONFIRMED": {"IN_PROGRESS", "ON_HOLD", "CANCELLED"},
    "IN_PROGRESS": {"IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELLED"},
    "ON_HOLD": {"IN_PROGRESS", "CANCELLED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
}


def _require_canonical_permission(actor, *, roles, module, action):
    if actor is None or not actor.is_active or actor.role.name not in roles:
        raise PermissionDenied(f"Missing canonical permission: {module}:{action}")
    FoundationPermissionService().require_permission(actor, module, action)


def _validate_idempotency(idempotency_key, request_hash):
    key = str(idempotency_key or "").strip()
    digest = str(request_hash or "").strip()
    if not key or len(key) > 64:
        raise ValidationError({"idempotency_key": "A key of at most 64 characters is required."})
    if not HASH_PATTERN.fullmatch(digest):
        raise ValidationError({"request_hash": "Request hash must be 64 hexadecimal characters."})
    return key, digest.lower()


def _validate_progress_percent(value):
    if isinstance(value, (bool, float)):
        raise ValidationError({"progress_percent": "Progress must be an integer from 0 through 100."})
    try:
        parsed_decimal = Decimal(str(value))
        parsed = int(parsed_decimal)
    except (InvalidOperation, TypeError, ValueError, OverflowError) as exc:
        raise ValidationError({"progress_percent": "Progress must be an integer from 0 through 100."}) from exc
    if not parsed_decimal.is_finite() or parsed_decimal != Decimal(parsed) or not 0 <= parsed <= 100:
        raise ValidationError({"progress_percent": "Progress must be an integer from 0 through 100."})
    return parsed


def _actor_identity(actor):
    return f"user:{actor.pk}", actor.full_name or actor.email


def _create_audit_event(
    *, actor, action, entity_id, old_status="", new_status="", reason="",
    metadata=None, correlation_id=None,
):
    actor_ref, actor_display = _actor_identity(actor)
    return AuditEvent.objects.create(
        actor_ref=actor_ref,
        actor_display=actor_display,
        actor_user=actor,
        action=action,
        entity_type="order",
        entity_id=str(entity_id),
        old_status=old_status,
        new_status=new_status,
        reason=reason,
        metadata=metadata or {},
        correlation_id=correlation_id or uuid.uuid4(),
    )


def _line_snapshot(line):
    return {
        "line_number": line.line_number,
        "source_quotation_line_id": line.pk,
        "source_rfq_line_id": line.source_rfq_line_id,
        "description": line.description,
        "part_code": line.part_code_snapshot,
        "material": line.material_snapshot,
        "quantity": str(line.quantity),
        "unit": line.unit,
        "unit_price": str(line.unit_price),
        "discount": str(line.discount),
        "line_subtotal": str(line.line_subtotal),
        "line_total": str(line.line_total),
    }


def _quotation_snapshot(quotation, lines):
    return {
        "quotation_id": quotation.pk,
        "quotation_number": quotation.quotation_number,
        "quotation_family_number": quotation.rfq.quotation_family_number,
        "revision": quotation.revision,
        "rfq_id": quotation.rfq_id,
        "currency": quotation.currency,
        "valid_from": quotation.valid_from.isoformat(),
        "valid_until": quotation.valid_until.isoformat(),
        "subtotal": str(quotation.subtotal),
        "discount_total": str(quotation.discount_total),
        "tax_amount": str(quotation.tax_amount),
        "total": str(quotation.total),
        "terms": quotation.terms,
        "sent_at": quotation.sent_at.isoformat() if quotation.sent_at else None,
        "rfq_snapshot": deepcopy(quotation.rfq_snapshot),
        "lines": [_line_snapshot(line) for line in lines],
    }


def _validate_quotation_financials(quotation, lines):
    if not lines:
        raise ValidationError({"quotation": "Accepted quotation must contain at least one line."})
    for line in lines:
        expected = calculate_line_amounts(
            quantity=line.quantity,
            unit_price=line.unit_price,
            discount=line.discount,
            currency=quotation.currency,
        )
        if any(getattr(line, field) != value for field, value in expected.items()):
            raise ValidationError({"quotation": "Quotation line totals do not match backend calculations."})
    expected_header = calculate_header_amounts(
        line_subtotals=[line.line_subtotal for line in lines],
        discount_total=quotation.discount_total,
        tax_amount=quotation.tax_amount,
        currency=quotation.currency,
    )
    if any(getattr(quotation, field) != value for field, value in expected_header.items()):
        raise ValidationError({"quotation": "Quotation totals do not match backend calculations."})


def _after_order_header_created(order):
    """Test seam for proving rollback immediately after header persistence."""


def _after_order_evidence_created(order):
    """Test seam for proving rollback after lines and event evidence persistence."""


def _after_order_transition_saved(order):
    """Test seam for proving rollback after a progress state save."""


def convert_accepted_quotation(
    *, quotation_id, actor_id, idempotency_key, request_hash, correlation_id=None,
):
    """Convert one eligible accepted quotation to one immutable canonical order."""
    key, digest = _validate_idempotency(idempotency_key, request_hash)
    actor = FoundationUser.objects.select_related("role").get(pk=actor_id)
    _require_canonical_permission(
        actor, roles=CONVERSION_ROLES, module="quotation", action="convert"
    )
    rfq_id = SalesQuotation.objects.only("rfq_id").get(pk=quotation_id).rfq_id
    if rfq_id is None:
        raise ValidationError({"quotation": "A canonical RFQ source is required."})

    with transaction.atomic():
        rfq = SalesRfq.objects.select_for_update().get(pk=rfq_id)
        quotation = SalesQuotation.objects.select_for_update().get(pk=quotation_id)

        existing_key = TransactionOrder.objects.filter(idempotency_key=key).first()
        if existing_key:
            if existing_key.request_hash == digest and existing_key.source_quotation_id == quotation.pk:
                return existing_key
            raise ValidationError({"idempotency_key": "Key was already used for another request."})
        if TransactionOrder.objects.filter(source_quotation=quotation).exists():
            raise ValidationError({"quotation": "This quotation already has a sales order."})
        if quotation.data_contract != "MVP_V1" or quotation.workflow_status != "ACCEPTED":
            raise ValidationError({"quotation": "Only an MVP_V1 ACCEPTED quotation can be converted."})
        if quotation.customer_id is None or quotation.rfq_id != rfq.pk:
            raise ValidationError({"quotation": "Quotation source relationships are incomplete."})
        if not quotation.customer_snapshot or not quotation.rfq_snapshot or quotation.sent_at is None:
            raise ValidationError({"quotation": "Sent customer and RFQ snapshots are required."})

        decision = SalesQuotationCustomerDecision.objects.filter(
            quotation=quotation, decision="ACCEPTED"
        ).first()
        if decision is None:
            raise ValidationError({"quotation": "Accepted customer decision evidence is required."})
        decision_date = timezone.localdate(decision.decided_at)
        today = timezone.localdate()
        if not quotation.valid_from <= decision_date <= quotation.valid_until:
            raise ValidationError({"quotation": "Quotation was not valid when accepted."})
        if today > quotation.valid_until:
            raise ValidationError({"quotation": "Expired quotations cannot be converted."})
        if rfq.required_delivery_date < today:
            raise ValidationError({"rfq": "Expected delivery date cannot precede the order date."})

        lines = list(
            SalesQuotationLine.objects.select_for_update()
            .filter(quotation=quotation)
            .order_by("line_number", "id")
        )
        if any(line.data_contract != "MVP_V1" for line in lines):
            raise ValidationError({"quotation": "All quotation lines must use the MVP_V1 contract."})
        _validate_quotation_financials(quotation, lines)

        ordered_at = timezone.now()
        order = TransactionOrder(
            data_contract="MVP_V1",
            source_quotation=quotation,
            source_rfq=rfq,
            order_number=allocate_business_number("SO", now=ordered_at),
            customer=quotation.customer,
            project_name=rfq.project_name,
            workflow_status="CONFIRMED",
            currency=quotation.currency,
            subtotal=quotation.subtotal,
            discount_total=quotation.discount_total,
            tax_amount=quotation.tax_amount,
            total_amount=quotation.total,
            customer_snapshot=deepcopy(quotation.customer_snapshot),
            quotation_snapshot=_quotation_snapshot(quotation, lines),
            ordered_at=ordered_at,
            expected_delivery_date=rfq.required_delivery_date,
            progress_percent=0,
            source_quotation_sent_at=quotation.sent_at,
            idempotency_key=key,
            request_hash=digest,
            created_by=actor,
            updated_by=actor,
        )
        order.full_clean()
        order._phase3d_conversion_authorized = True
        try:
            order.save(force_insert=True)
        finally:
            del order._phase3d_conversion_authorized
        _after_order_header_created(order)

        for line in lines:
            item = TransactionOrderItem(
                order=order,
                data_contract="MVP_V1",
                line_number=line.line_number,
                source_quotation_line=line,
                product_id=line.product_id,
                drawing_code=line.part_code_snapshot,
                material_name=line.material_snapshot,
                description_snapshot=line.description,
                part_code_snapshot=line.part_code_snapshot,
                material_snapshot=line.material_snapshot,
                quantity=line.quantity,
                unit=line.unit,
                unit_price=line.unit_price,
                line_total=line.line_total,
            )
            item.full_clean()
            item._phase3d_conversion_authorized = True
            try:
                item.save(force_insert=True)
            finally:
                del item._phase3d_conversion_authorized

        OrderProgressEvent.objects.create(
            order=order,
            from_status="",
            to_status="CONFIRMED",
            progress_percent=0,
            milestone_note="Order converted from accepted quotation",
            actor=actor,
        )
        _create_audit_event(
            actor=actor,
            action="order.converted",
            entity_id=order.pk,
            new_status="CONFIRMED",
            metadata={
                "source_quotation_id": quotation.pk,
                "source_quotation_number": quotation.quotation_number,
                "source_rfq_id": rfq.pk,
                "source_rfq_number": rfq.rfq_number,
                "line_count": len(lines),
                "currency": quotation.currency,
            },
            correlation_id=correlation_id,
        )
        rfq.status = "CLOSED"
        rfq.closure_reason = f"Converted to sales order {order.order_number}"
        rfq.updated_by = actor
        rfq.save(update_fields=["status", "closure_reason", "updated_by", "updated_at"])
        _after_order_evidence_created(order)
        return order


def _transition_permission(current_status, target_status):
    if target_status == "ON_HOLD":
        return "hold", "order.held"
    if target_status == "CANCELLED":
        return "cancel", "order.cancelled"
    if target_status == "COMPLETED":
        return "complete", "order.completed"
    if current_status == "ON_HOLD" and target_status == "IN_PROGRESS":
        return "resume", "order.resumed"
    return "progress", "order.progress_changed"


def transition_order(
    *, order_id, actor_id, target_status, progress_percent,
    milestone_note="", reason="", correlation_id=None,
):
    """Apply one authorized canonical order transition with two evidence rows."""
    target_status = str(target_status or "").strip().upper()
    progress = _validate_progress_percent(progress_percent)
    reason = str(reason or "").strip()
    milestone_note = str(milestone_note or "").strip()
    if len(milestone_note) > 240:
        raise ValidationError({"milestone_note": "Milestone note must not exceed 240 characters."})
    if target_status in {"ON_HOLD", "CANCELLED"} and not reason:
        raise ValidationError({"reason": "Hold and cancellation transitions require a reason."})
    if target_status == "COMPLETED" and progress != 100:
        raise ValidationError({"progress_percent": "Completion requires 100 percent progress."})

    actor = FoundationUser.objects.select_related("role").get(pk=actor_id)
    with transaction.atomic():
        order = TransactionOrder.objects.select_for_update().get(pk=order_id)
        if order.data_contract != "MVP_V1" or order.workflow_status is None:
            raise PermissionDenied("Legacy orders cannot use canonical progress commands.")
        allowed = ALLOWED_TRANSITIONS.get(order.workflow_status, set())
        if target_status not in allowed:
            raise ValidationError({"workflow_status": f"Cannot transition from {order.workflow_status} to {target_status}."})
        permission, audit_action = _transition_permission(order.workflow_status, target_status)
        _require_canonical_permission(
            actor, roles=PROGRESS_ROLES, module="order", action=permission
        )
        if target_status == "IN_PROGRESS" and order.expected_delivery_date is None:
            raise ValidationError({"expected_delivery_date": "Expected delivery date is required before work starts."})
        if target_status == order.workflow_status and progress == order.progress_percent:
            raise ValidationError({"progress_percent": "Progress command must advance recorded progress."})

        previous_status = order.workflow_status
        order.workflow_status = target_status
        order.progress_percent = progress
        order.updated_by = actor
        if target_status == "ON_HOLD":
            order.hold_reason = reason
        elif previous_status == "ON_HOLD" and target_status == "IN_PROGRESS":
            order.hold_reason = ""
        if target_status == "CANCELLED":
            order.cancel_reason = reason
        if target_status == "COMPLETED":
            order.completed_at_v1 = timezone.now()
        order.full_clean()
        order._phase3d_transition_authorized = True
        try:
            order.save(update_fields=[
                "workflow_status", "progress_percent", "hold_reason", "cancel_reason",
                "completed_at_v1", "updated_by", "updated_at",
            ])
        finally:
            del order._phase3d_transition_authorized
        _after_order_transition_saved(order)

        OrderProgressEvent.objects.create(
            order=order,
            from_status=previous_status,
            to_status=target_status,
            progress_percent=progress,
            milestone_note=milestone_note,
            reason=reason,
            actor=actor,
        )
        _create_audit_event(
            actor=actor,
            action=audit_action,
            entity_id=order.pk,
            old_status=previous_status,
            new_status=target_status,
            reason=reason,
            metadata={"progress_percent": progress, "milestone_note": milestone_note},
            correlation_id=correlation_id,
        )
        return order
