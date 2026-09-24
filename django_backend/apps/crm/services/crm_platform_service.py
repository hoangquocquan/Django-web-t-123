"""Django-owned CRM platform service layer."""

from __future__ import annotations

from django.db import transaction

from apps.business_core.models import BusinessCustomer
from apps.crm.models import CrmCustomerProfile, CrmInteraction, CrmNote, CrmTask, CrmTimelineEvent


class CrmPlatformService:
    """Own CRM profile, interaction, and timeline writes in Django."""

    def list_customers(self):
        """Return Django-owned business customers with CRM profile if present."""
        return BusinessCustomer.objects.prefetch_related("crm_interactions", "crm_notes", "crm_tasks").all()

    @transaction.atomic
    def create_customer(self, data, owner=None):
        """Create a business customer and CRM profile."""
        customer = BusinessCustomer.objects.create(
            company_name=data.get("company_name", ""),
            contact_name=data["contact_name"],
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            country=data.get("country", "Vietnam"),
            status=data.get("status", "lead"),
            notes=data.get("notes", ""),
        )
        CrmCustomerProfile.objects.create(
            customer=customer,
            segment=data.get("segment", "standard"),
            lifecycle_stage=data.get("lifecycle_stage", "lead"),
            preferred_contact_method=data.get("preferred_contact_method", ""),
            assigned_owner=owner,
            summary=data.get("summary", ""),
        )
        CrmTimelineEvent.objects.create(
            customer=customer,
            event_type="customer_created",
            title="Customer profile created",
            payload={"source": "crm_platform"},
        )
        return customer

    def get_customer_context(self, customer_id):
        """Return a complete CRM context for a customer."""
        customer = BusinessCustomer.objects.get(id=customer_id)
        profile = getattr(customer, "crm_profile", None)
        return {
            "customer": customer,
            "profile": profile,
            "interactions": customer.crm_interactions.all(),
            "notes": customer.crm_notes.all(),
            "tasks": customer.crm_tasks.all(),
            "timeline": customer.crm_timeline_events.all(),
        }

    @transaction.atomic
    def add_interaction(self, customer_id, data, actor=""):
        """Add CRM interaction and timeline event."""
        customer = BusinessCustomer.objects.get(id=customer_id)
        interaction = CrmInteraction.objects.create(
            customer=customer,
            interaction_type=data.get("interaction_type", "note"),
            subject=data["subject"],
            content=data.get("content", ""),
            occurred_at=data.get("occurred_at", ""),
            created_by=actor,
        )
        CrmTimelineEvent.objects.create(
            customer=customer,
            event_type="interaction",
            title=interaction.subject,
            payload={"interaction_id": interaction.id, "type": interaction.interaction_type},
        )
        return interaction

    def add_note(self, customer_id, note, actor=""):
        """Add a customer note."""
        customer = BusinessCustomer.objects.get(id=customer_id)
        crm_note = CrmNote.objects.create(customer=customer, note=note, created_by=actor)
        CrmTimelineEvent.objects.create(
            customer=customer,
            event_type="note",
            title="CRM note added",
            payload={"note_id": crm_note.id},
        )
        return crm_note

    def create_task(self, customer_id, data, owner=None):
        """Create a CRM task."""
        customer = BusinessCustomer.objects.get(id=customer_id)
        task = CrmTask.objects.create(
            customer=customer,
            title=data["title"],
            due_date=data.get("due_date", ""),
            status=data.get("status", "open"),
            owner=owner,
        )
        CrmTimelineEvent.objects.create(
            customer=customer,
            event_type="task",
            title=task.title,
            payload={"task_id": task.id},
        )
        return task
