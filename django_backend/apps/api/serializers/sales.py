"""Serializer helpers for read-only sales quotation API responses."""

from apps.api.serializers.catalog import material_to_dict, product_to_dict
from apps.api.serializers.crm import customer_to_dict


def quote_file_to_dict(file_obj):
    """Convert quote file metadata without touching the physical file."""
    return {
        "id": file_obj.id,
        "file_name": file_obj.file_name,
        "file_url": file_obj.file_url,
        "file_type": file_obj.file_type,
        "uploaded_at": file_obj.uploaded_at,
    }


def quote_item_to_dict(item):
    """Convert one quote line item while preserving linked master data."""
    return {
        "id": item.id,
        "drawing_code": item.drawing_code,
        "quantity": item.quantity,
        "tolerance": item.tolerance,
        "note": item.note,
        "product": product_to_dict(item.product) if item.product else None,
        "material": material_to_dict(item.material) if item.material else None,
    }


def quote_to_dict(quote):
    """Convert a quote header into JSON."""
    return {
        "id": quote.id,
        "project_name": quote.project_name,
        "message": quote.message,
        "status": quote.status,
        "assigned_to": quote.assigned_to,
        "internal_note": quote.internal_note,
        "quoted_at": quote.quoted_at,
        "completed_at": quote.completed_at,
        "created_at": quote.created_at,
        "customer": customer_to_dict(quote.customer),
    }


def quote_detail_to_dict(detail):
    """Convert quote detail service result into JSON."""
    quote = quote_to_dict(detail["quote"])
    quote["items"] = [quote_item_to_dict(item) for item in detail["items"]]
    quote["files"] = [quote_file_to_dict(file_obj) for file_obj in detail["files"]]
    return quote


def sales_lead_to_dict(lead):
    """Convert a Django-owned sales lead into API JSON."""
    return {
        "id": lead.id,
        "lead_source": lead.lead_source,
        "company": lead.company,
        "contact_person": lead.contact_person,
        "email": lead.email,
        "phone": lead.phone,
        "industry": lead.industry,
        "status": lead.status,
        "priority": lead.priority,
        "owner": lead.owner.email if lead.owner else None,
        "notes": lead.notes,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
    }


def sales_opportunity_to_dict(opportunity):
    """Convert a Django-owned opportunity into API JSON."""
    return {
        "id": opportunity.id,
        "lead_id": opportunity.lead_id,
        "customer_id": opportunity.customer_id,
        "title": opportunity.title,
        "value": str(opportunity.value),
        "probability": opportunity.probability,
        "expected_close_date": opportunity.expected_close_date,
        "sales_owner": opportunity.sales_owner.email if opportunity.sales_owner else None,
        "status": opportunity.status,
        "notes": opportunity.notes,
        "created_at": opportunity.created_at.isoformat() if opportunity.created_at else None,
    }


def sales_quotation_line_to_dict(line):
    """Convert a managed quotation line into API JSON."""
    return {
        "id": line.id,
        "product_id": line.product_id,
        "description": line.description,
        "quantity": str(line.quantity),
        "unit_price": str(line.unit_price),
        "discount": str(line.discount),
        "line_total": str(line.line_total),
    }


def sales_quotation_to_dict(quotation):
    """Convert a Django-owned quotation into API JSON."""
    return {
        "id": quotation.id,
        "opportunity_id": quotation.opportunity_id,
        "customer_id": quotation.customer_id,
        "quotation_number": quotation.quotation_number,
        "version": quotation.version,
        "status": quotation.status,
        "approval_status": quotation.approval_status,
        "subtotal": str(quotation.subtotal),
        "discount_total": str(quotation.discount_total),
        "total": str(quotation.total),
        "created_by": quotation.created_by.email if quotation.created_by else None,
        "lines": [sales_quotation_line_to_dict(line) for line in quotation.lines.all()],
        "created_at": quotation.created_at.isoformat() if quotation.created_at else None,
    }
