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
