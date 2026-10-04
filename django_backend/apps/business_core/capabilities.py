"""Transactional publication workflow for managed Capability content."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.transaction_domain.models import AuditEvent

from .models import Capability

ALLOWED_TRANSITIONS = {
    "DRAFT": {"REVIEW"},
    "REVIEW": {"APPROVED"},
    "APPROVED": {"PUBLISHED"},
    "PUBLISHED": {"ARCHIVED"},
}

EDITABLE_FIELDS = {
    "title",
    "slug",
    "short_description",
    "description",
    "image",
    "technology_type",
    "process_category",
    "display_order",
    "is_active",
    "seo_title",
    "seo_description",
}

TRANSITION_AUDIT_ACTIONS = {
    ("DRAFT", "REVIEW"): "capability.submitted",
    ("REVIEW", "APPROVED"): "capability.approved",
    ("APPROVED", "PUBLISHED"): "capability.published",
    ("PUBLISHED", "ARCHIVED"): "capability.archived",
}


def _audit(*, actor, capability, action, old_status, new_status):
    if actor is None or not getattr(actor, "pk", None):
        raise ValidationError("An authenticated audit actor is required.")
    return AuditEvent.objects.create(
        actor_ref=f"user:{actor.pk}",
        actor_display=actor.full_name or actor.email,
        actor_user=actor,
        action=action,
        entity_type="capability",
        entity_id=str(capability.pk),
        old_status=old_status,
        new_status=new_status,
    )


def _validate_publishable(capability):
    if not capability.is_active:
        raise ValidationError("An inactive capability cannot be published.")
    if not capability.title.strip() or not capability.slug.strip():
        raise ValidationError("Title and slug are required for publication.")
    if not capability.description.strip():
        raise ValidationError("A reviewed description is required for publication.")


class CapabilityPublicationService:
    """Create, edit and transition Capability records with append-only audit."""

    def list_all(self):
        return Capability.objects.all()

    def list_published(self):
        return self.list_all().filter(
            status="PUBLISHED",
            is_active=True,
            published_at__isnull=False,
            published_at__lte=timezone.now(),
        )

    def get(self, capability_id):
        return self.list_all().get(pk=capability_id)

    @transaction.atomic
    def create(self, *, actor, **fields):
        fields.pop("status", None)
        fields.pop("published_at", None)
        unsupported = set(fields) - EDITABLE_FIELDS
        if unsupported:
            raise ValidationError("Unsupported capability fields.")
        capability = Capability.objects.create(status="DRAFT", **fields)
        _audit(
            actor=actor,
            capability=capability,
            action="capability.created",
            old_status="",
            new_status="DRAFT",
        )
        return capability

    @transaction.atomic
    def update(self, capability, *, actor, **fields):
        locked = self.list_all().select_for_update().get(pk=capability.pk)
        target_status = fields.pop("status", None)
        fields.pop("published_at", None)
        unsupported = set(fields) - EDITABLE_FIELDS
        if unsupported:
            raise ValidationError("Unsupported capability fields.")
        if fields and locked.status != "DRAFT":
            raise ValidationError("Capability content can only be edited in DRAFT status.")
        for field_name, value in fields.items():
            setattr(locked, field_name, value)
        if fields:
            locked.save(update_fields=[*fields, "updated_at"])
            _audit(
                actor=actor,
                capability=locked,
                action="capability.updated",
                old_status=locked.status,
                new_status=locked.status,
            )
        if target_status and target_status != locked.status:
            return self.transition(locked, target_status, actor=actor)
        return locked

    @transaction.atomic
    def transition(self, capability, target_status, *, actor):
        locked = self.list_all().select_for_update().get(pk=capability.pk)
        old_status = locked.status
        if target_status not in ALLOWED_TRANSITIONS.get(old_status, set()):
            raise ValidationError(
                f"Invalid capability transition: {old_status} -> {target_status}."
            )
        if target_status == "PUBLISHED":
            _validate_publishable(locked)
            locked.published_at = timezone.now()
        locked.status = target_status
        locked.save(update_fields=["status", "published_at", "updated_at"])
        _audit(
            actor=actor,
            capability=locked,
            action=TRANSITION_AUDIT_ACTIONS[(old_status, target_status)],
            old_status=old_status,
            new_status=target_status,
        )
        return locked


