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


def crm_profile_to_dict(profile):
    """Convert a managed CRM profile into API JSON."""
    if not profile:
        return None
    return {
        "segment": profile.segment,
        "lifecycle_stage": profile.lifecycle_stage,
        "preferred_contact_method": profile.preferred_contact_method,
        "assigned_owner": profile.assigned_owner.email if profile.assigned_owner else None,
        "summary": profile.summary,
    }


def business_customer_to_crm_dict(customer):
    """Convert a Django-owned business customer into CRM API JSON."""
    return {
        "id": customer.id,
        "company_name": customer.company_name,
        "contact_name": customer.contact_name,
        "email": customer.email,
        "phone": customer.phone,
        "country": customer.country,
        "status": customer.status,
        "notes": customer.notes,
        "profile": crm_profile_to_dict(getattr(customer, "crm_profile", None)),
        "created_at": customer.created_at.isoformat() if customer.created_at else None,
    }


def crm_interaction_to_dict(interaction):
    """Convert a CRM interaction into API JSON."""
    return {
        "id": interaction.id,
        "customer_id": interaction.customer_id,
        "interaction_type": interaction.interaction_type,
        "subject": interaction.subject,
        "content": interaction.content,
        "occurred_at": interaction.occurred_at,
        "created_by": interaction.created_by,
        "created_at": interaction.created_at.isoformat() if interaction.created_at else None,
    }


def crm_note_to_dict(note):
    """Convert a Django-owned CRM note into API JSON."""
    return {
        "id": note.id,
        "customer_id": note.customer_id,
        "note": note.note,
        "created_by": note.created_by,
        "created_at": note.created_at.isoformat() if note.created_at else None,
    }


def crm_task_to_dict(task):
    """Convert a CRM task into API JSON."""
    return {
        "id": task.id,
        "customer_id": task.customer_id,
        "title": task.title,
        "due_date": task.due_date,
        "status": task.status,
        "owner": task.owner.email if task.owner else None,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }


def crm_timeline_to_dict(event):
    """Convert a CRM timeline event into API JSON."""
    return {
        "id": event.id,
        "customer_id": event.customer_id,
        "event_type": event.event_type,
        "title": event.title,
        "payload": event.payload,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


def crm_customer_context_to_dict(context):
    """Convert full CRM context into API JSON."""
    return {
        "customer": business_customer_to_crm_dict(context["customer"]),
        "interactions": [crm_interaction_to_dict(item) for item in context["interactions"]],
        "notes": [crm_note_to_dict(item) for item in context["notes"]],
        "tasks": [crm_task_to_dict(item) for item in context["tasks"]],
        "timeline": [crm_timeline_to_dict(item) for item in context["timeline"]],
    }
