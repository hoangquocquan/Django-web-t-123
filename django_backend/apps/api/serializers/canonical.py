"""Explicit safe serializers for canonical Phase 4A read APIs."""

from __future__ import annotations

from decimal import Decimal

from django.utils import timezone


SAFE_AUDIT_METADATA_KEYS = frozenset(
    {
        "source_quotation_id",
        "source_quotation_number",
        "source_rfq_id",
        "source_rfq_number",
        "line_count",
        "progress_percent",
        "milestone_note",
    }
)


def _datetime(value):
    if value is None:
        return None
    if timezone.is_naive(value):
        value = timezone.make_aware(value)
    return timezone.localtime(value).isoformat()


def _date(value):
    return value.isoformat() if value else None


def _decimal(value):
    return str(value if isinstance(value, Decimal) else Decimal(value or 0))


def _user_id(user_id):
    return user_id


def _legacy(instance, **fields):
    if instance.data_contract != "LEGACY":
        return None
    return {"representation": "LEGACY", **fields}


def customer_to_dict(customer):
    return {
        "id": customer.pk,
        "data_contract": customer.data_contract,
        "customer_code": customer.customer_code,
        "company_name": customer.company_name,
        "contact_name": customer.contact_name,
        "email": customer.email,
        "phone": customer.phone,
        "country": customer.country,
        "status": customer.status if customer.data_contract == "MVP_V1" else None,
        "archived_at": _datetime(customer.archived_at),
        "created_by_id": _user_id(customer.created_by_id),
        "updated_by_id": _user_id(customer.updated_by_id),
        "created_at": _datetime(customer.created_at),
        "updated_at": _datetime(customer.updated_at),
        "compatibility": _legacy(
            customer,
            legacy_customer_id=customer.legacy_customer_id,
            legacy_status=customer.status,
        ),
    }


def material_to_dict(material):
    return {
        "id": material.pk,
        "data_contract": material.data_contract,
        "material_code": material.material_code,
        "name": material.name,
        "standard": material.standard,
        "grade": material.grade,
        "description": material.description,
        "is_active": material.is_active,
        "created_by_id": _user_id(material.created_by_id),
        "updated_by_id": _user_id(material.updated_by_id),
        "created_at": _datetime(material.created_at),
        "updated_at": _datetime(material.updated_at),
        "compatibility": _legacy(
            material,
            legacy_material_id=material.legacy_material_id,
        ),
    }


def part_to_dict(part):
    return {
        "id": part.pk,
        "data_contract": part.data_contract,
        "part_code": part.part_code,
        "name": part.name,
        "revision": part.revision,
        "unit": part.unit,
        "default_material_id": part.default_material_id,
        "tolerance": part.tolerance,
        "technical_requirements": part.technical_requirements,
        "is_active": part.is_active,
        "archived_at": _datetime(part.archived_at),
        "created_by_id": _user_id(part.created_by_id),
        "updated_by_id": _user_id(part.updated_by_id),
        "created_at": _datetime(part.created_at),
        "updated_at": _datetime(part.updated_at),
        "compatibility": _legacy(
            part,
            legacy_product_id=part.legacy_product_id,
            legacy_status=part.status,
            legacy_sku=part.sku,
        ),
    }


def rfq_to_dict(rfq):
    return {
        "id": rfq.pk,
        "data_contract": rfq.data_contract,
        "rfq_number": rfq.rfq_number,
        "quotation_family_number": rfq.quotation_family_number or None,
        "customer_id": rfq.customer_id,
        "status": rfq.status if rfq.data_contract == "MVP_V1" else None,
        "project_name": rfq.project_name,
        "notes": rfq.notes,
        "quote_due_at": _date(rfq.quote_due_at),
        "required_delivery_date": _date(rfq.required_delivery_date),
        "assigned_to_id": _user_id(rfq.assigned_to_id),
        "closure_reason": rfq.closure_reason,
        "created_by_id": _user_id(rfq.created_by_id),
        "updated_by_id": _user_id(rfq.updated_by_id),
        "created_at": _datetime(rfq.created_at),
        "updated_at": _datetime(rfq.updated_at),
        "compatibility": _legacy(
            rfq,
            legacy_quote_request_id=rfq.legacy_quote_request_id,
            legacy_status=rfq.status,
        ),
    }


def rfq_line_to_dict(line):
    return {
        "id": line.pk,
        "rfq_id": line.rfq_id,
        "line_number": line.line_number,
        "part_id": line.part_id,
        "material_id": line.material_id,
        "description": line.description,
        "quantity": _decimal(line.quantity),
        "unit": line.unit,
        "required_delivery_date": _date(line.required_delivery_date),
        "tolerance": line.tolerance,
        "technical_notes": line.technical_notes,
        "drawing_required": line.drawing_required,
        "created_at": _datetime(line.created_at),
        "updated_at": _datetime(line.updated_at),
    }


def rfq_document_to_dict(document):
    safe_filename = str(document.original_filename).replace("\\", "/").rsplit("/", 1)[-1]
    return {
        "id": document.pk,
        "rfq_id": document.rfq_id,
        "rfq_line_id": document.rfq_line_id,
        "document_group_id": str(document.document_group_id),
        "version": document.version,
        "original_filename": safe_filename,
        "mime_type": document.mime_type,
        "size_bytes": document.size_bytes,
        "checksum_sha256": document.checksum_sha256,
        "document_revision": document.document_revision,
        "replaces_id": document.replaces_id,
        "uploaded_by_id": _user_id(document.uploaded_by_id),
        "uploaded_at": _datetime(document.uploaded_at),
    }


def technical_review_to_dict(review):
    return {
        "id": review.pk,
        "rfq_id": review.rfq_id,
        "reviewer_id": _user_id(review.reviewer_id),
        "decision": review.decision,
        "reason": review.reason,
        "notes": review.notes,
        "requested_fields": list(review.requested_fields or []),
        "created_at": _datetime(review.created_at),
    }


def quotation_summary_to_dict(quotation):
    family_number = quotation.rfq.quotation_family_number if quotation.rfq_id else None
    return {
        "id": quotation.pk,
        "data_contract": quotation.data_contract,
        "quotation_family_number": family_number or None,
        "quotation_number": quotation.quotation_number,
        "revision": quotation.revision,
        "rfq_id": quotation.rfq_id,
        "customer_id": quotation.customer_id,
        "workflow_status": (
            quotation.workflow_status if quotation.data_contract == "MVP_V1" else None
        ),
        "currency": quotation.currency,
        "valid_from": _date(quotation.valid_from),
        "valid_until": _date(quotation.valid_until),
        "subtotal": _decimal(quotation.subtotal),
        "discount_total": _decimal(quotation.discount_total),
        "tax_amount": _decimal(quotation.tax_amount),
        "total": _decimal(quotation.total),
        "sent_at": _datetime(quotation.sent_at),
        "created_by_id": _user_id(quotation.created_by_id),
        "created_at": _datetime(quotation.created_at),
        "updated_at": _datetime(quotation.updated_at),
        "compatibility": _legacy(
            quotation,
            legacy_status=quotation.status,
            legacy_approval_status=quotation.approval_status,
            legacy_version=quotation.version,
        ),
    }


def quotation_to_dict(quotation):
    data = quotation_summary_to_dict(quotation)
    data.update(
        {
            "terms": quotation.terms,
            "customer_snapshot": {
                key: quotation.customer_snapshot.get(key)
                for key in ("id", "customer_code", "company_name", "contact_name")
                if key in quotation.customer_snapshot
            },
            "rfq_snapshot": {
                key: quotation.rfq_snapshot.get(key)
                for key in (
                    "id",
                    "rfq_number",
                    "project_name",
                    "quote_due_at",
                    "required_delivery_date",
                )
                if key in quotation.rfq_snapshot
            },
            "updated_by_id": _user_id(quotation.updated_by_id),
        }
    )
    return data


def quotation_family_to_dict(rfq):
    revisions = list(rfq.quotations.all())
    return {
        "quotation_family_number": rfq.quotation_family_number,
        "rfq_id": rfq.pk,
        "rfq_number": rfq.rfq_number,
        "customer_id": rfq.customer_id,
        "revision_count": len(revisions),
        "revisions": [quotation_summary_to_dict(item) for item in revisions],
    }


def quotation_line_to_dict(line):
    return {
        "id": line.pk,
        "quotation_id": line.quotation_id,
        "data_contract": line.data_contract,
        "line_number": line.line_number,
        "source_rfq_line_id": line.source_rfq_line_id,
        "part_id": line.product_id,
        "description": line.description,
        "part_code_snapshot": line.part_code_snapshot,
        "material_snapshot": line.material_snapshot,
        "unit": line.unit,
        "quantity": _decimal(line.quantity),
        "unit_price": _decimal(line.unit_price),
        "discount": _decimal(line.discount),
        "line_subtotal": _decimal(line.line_subtotal),
        "line_total": _decimal(line.line_total),
        "created_at": _datetime(line.created_at),
    }


def approval_decision_to_dict(decision):
    return {
        "id": decision.pk,
        "quotation_id": decision.quotation_id,
        "reviewer_id": _user_id(decision.reviewer_id),
        "decision": decision.decision,
        "reason": decision.reason,
        "notes": decision.notes,
        "decided_at": _datetime(decision.decided_at),
    }


def customer_decision_to_dict(decision):
    return {
        "id": decision.pk,
        "quotation_id": decision.quotation_id,
        "recorded_by_id": _user_id(decision.recorded_by_id),
        "decision": decision.decision,
        "reason": decision.reason,
        "contact_evidence_recorded": bool(decision.contact_snapshot),
        "decision_evidence_recorded": bool(decision.evidence),
        "decided_at": _datetime(decision.decided_at),
    }


def order_to_dict(order):
    return {
        "id": order.pk,
        "data_contract": order.data_contract,
        "order_number": order.order_number,
        "source_quotation_id": order.source_quotation_id,
        "source_rfq_id": order.source_rfq_id,
        "customer_id": order.customer_id,
        "workflow_status": order.workflow_status if order.data_contract == "MVP_V1" else None,
        "currency": order.currency,
        "subtotal": _decimal(order.subtotal),
        "discount_total": _decimal(order.discount_total),
        "tax_amount": _decimal(order.tax_amount),
        "total_amount": _decimal(order.total_amount),
        "ordered_at": _datetime(order.ordered_at),
        "expected_delivery_date": _date(order.expected_delivery_date),
        "progress_percent": order.progress_percent,
        "hold_reason": order.hold_reason,
        "cancel_reason": order.cancel_reason,
        "source_quotation_sent_at": _datetime(order.source_quotation_sent_at),
        "completed_at": _datetime(order.completed_at_v1),
        "created_by_id": _user_id(order.created_by_id),
        "updated_by_id": _user_id(order.updated_by_id),
        "created_at": _datetime(order.created_at),
        "updated_at": _datetime(order.updated_at),
        "compatibility": _legacy(
            order,
            legacy_quote_request_id=order.legacy_quote_request_id,
            legacy_status=order.status,
            legacy_quoted_at=order.quoted_at,
            legacy_completed_at=order.completed_at,
        ),
    }


def order_line_to_dict(line):
    return {
        "id": line.pk,
        "order_id": line.order_id,
        "data_contract": line.data_contract,
        "line_number": line.line_number,
        "source_quotation_line_id": line.source_quotation_line_id,
        "part_id": line.product_id,
        "description_snapshot": line.description_snapshot,
        "part_code_snapshot": line.part_code_snapshot,
        "material_snapshot": line.material_snapshot,
        "quantity": _decimal(line.quantity),
        "unit": line.unit,
        "unit_price": _decimal(line.unit_price),
        "line_total": _decimal(line.line_total),
        "compatibility": _legacy(
            line,
            legacy_quote_item_id=line.legacy_quote_item_id,
            legacy_drawing_code=line.drawing_code,
            legacy_material_name=line.material_name,
        ),
    }


def progress_event_to_dict(event):
    return {
        "id": event.pk,
        "order_id": event.order_id,
        "from_status": event.from_status or None,
        "to_status": event.to_status,
        "progress_percent": event.progress_percent,
        "milestone_note": event.milestone_note,
        "reason": event.reason,
        "actor_id": _user_id(event.actor_id),
        "created_at": _datetime(event.created_at),
    }


def audit_event_to_dict(event):
    safe_metadata = {
        key: value
        for key, value in (event.metadata or {}).items()
        if key in SAFE_AUDIT_METADATA_KEYS
        and isinstance(value, (str, int, float, bool, type(None)))
    }
    return {
        "id": event.pk,
        "actor_ref": event.actor_ref,
        "actor_display": event.actor_display,
        "action": event.action,
        "entity_type": event.entity_type,
        "entity_id": event.entity_id,
        "old_status": event.old_status or None,
        "new_status": event.new_status or None,
        "reason": event.reason,
        "metadata": safe_metadata,
        "correlation_id": str(event.correlation_id),
        "created_at": _datetime(event.created_at),
    }
