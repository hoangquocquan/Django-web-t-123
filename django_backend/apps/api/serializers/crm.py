"""Serializer helpers for read-only CRM API responses."""


def customer_note_to_dict(note):
    """Convert a customer note into JSON."""
    return {
        "id": note.id,
        "note": note.note,
        "created_by": note.created_by,
        "created_at": note.created_at,
    }


def customer_to_dict(customer):
    """Convert a customer ORM object into API-safe JSON."""
    return {
        "id": customer.id,
        "company_name": customer.company_name,
        "contact_name": customer.contact_name,
        "email": customer.email,
        "phone": customer.phone,
        "country": customer.country,
        "created_at": customer.created_at,
    }


def customer_detail_to_dict(detail):
    """Convert customer detail service result into JSON."""
    customer = customer_to_dict(detail["customer"])
    customer["notes"] = [customer_note_to_dict(note) for note in detail["notes"]]
    return customer


def contact_request_to_dict(contact):
    """Convert a public contact request into JSON for CMS operators."""
    return {
        "id": contact.id,
        "name": contact.name,
        "contact": contact.contact,
        "message": contact.message,
        "status": contact.status,
        "is_read": contact.is_read,
        "note": contact.note,
        "company": contact.company,
        "phone": contact.phone,
        "email": contact.email,
        "country": contact.country,
        "interested_product": contact.interested_product,
        "attachment_url": contact.attachment_url,
        "created_at": contact.created_at,
    }
