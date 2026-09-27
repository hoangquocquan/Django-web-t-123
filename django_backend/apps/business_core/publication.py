"""Publication workflow for public product projections."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.transaction_domain.models import AuditEvent

from .models import BusinessProduct, PublicProductProjection

ALLOWED_TRANSITIONS = {
    "DRAFT": {"REVIEW"},
    "REVIEW": {"DRAFT", "APPROVED"},
    "APPROVED": {"DRAFT", "PUBLISHED"},
    "PUBLISHED": {"ARCHIVED"},
    "ARCHIVED": {"DRAFT"},
}

EDITABLE_FIELDS = {
    "title",
    "slug",
    "public_description",
    "public_material",
    "public_specifications",
    "category",
    "main_image",
    "seo_title",
    "seo_description",
    "display_order",
}

TRANSITION_AUDIT_ACTIONS = {
    ("DRAFT", "REVIEW"): "public_product.submitted",
    ("REVIEW", "DRAFT"): "public_product.returned",
    ("REVIEW", "APPROVED"): "public_product.approved",
    ("APPROVED", "DRAFT"): "public_product.approval_revoked",
    ("APPROVED", "PUBLISHED"): "public_product.published",
    ("PUBLISHED", "ARCHIVED"): "public_product.archived",
    ("ARCHIVED", "DRAFT"): "public_product.restored",
}


def _audit(*, actor, projection, action, old_status, new_status):
    if actor is None or not getattr(actor, "pk", None):
        raise ValidationError("An authenticated audit actor is required.")
    return AuditEvent.objects.create(
        actor_ref=f"user:{actor.pk}",
        actor_display=actor.full_name or actor.email,
        actor_user=actor,
        action=action,
        entity_type="public_product",
        entity_id=str(projection.public_id),
        old_status=old_status,
        new_status=new_status,
    )


def _validate_structured_content(fields):
    material = fields.get("public_material")
    specifications = fields.get("public_specifications")
    if material is not None and not isinstance(material, dict):
        raise ValidationError("public_material must be an object.")
    if specifications is not None and not isinstance(specifications, list):
        raise ValidationError("public_specifications must be a list.")
    for specification in specifications or []:
        if not isinstance(specification, dict):
            raise ValidationError("Each public specification must be an object.")
        if set(specification) - {"label", "value"}:
            raise ValidationError("Public specifications only support label and value.")
        if not str(specification.get("label", "")).strip() or not str(
            specification.get("value", "")
        ).strip():
            raise ValidationError("Public specification label and value are required.")


def _validate_publishable(projection):
    if not projection.source_product.is_active or projection.source_product.archived_at:
        raise ValidationError("The source product is not eligible for publication.")
    if not projection.title.strip() or not projection.slug.strip():
        raise ValidationError("Title and slug are required for publication.")
    if not projection.public_description.strip():
        raise ValidationError("A reviewed public description is required for publication.")


class PublicProductPublicationService:
    """Create, edit and transition projections without mutating master products."""

    def list_all(self):
        return PublicProductProjection.objects.select_related("source_product").all()

    def list_published(self):
        return self.list_all().filter(
            publication_status="PUBLISHED",
            published_at__isnull=False,
            published_at__lte=timezone.now(),
            source_product__is_active=True,
            source_product__archived_at__isnull=True,
        )

    def get(self, projection_id):
        return self.list_all().get(pk=projection_id)

    @transaction.atomic
    def create(self, *, source_product, actor, **fields):
        if not isinstance(source_product, BusinessProduct):
            raise ValidationError("A valid source product is required.")
        if PublicProductProjection.objects.filter(source_product=source_product).exists():
            raise ValidationError("This source product already has a public projection.")
        _validate_structured_content(fields)
        fields.pop("publication_status", None)
        fields.pop("published_at", None)
        projection = PublicProductProjection.objects.create(
            source_product=source_product,
            publication_status="DRAFT",
            **fields,
        )
        _audit(
            actor=actor,
            projection=projection,
            action="public_product.created",
            old_status="",
            new_status="DRAFT",
        )
        return projection

    @transaction.atomic
    def update(self, projection, *, actor, **fields):
        locked = self.list_all().select_for_update().get(pk=projection.pk)
        target_status = fields.pop("publication_status", None)
        fields.pop("published_at", None)
        unsupported = set(fields) - EDITABLE_FIELDS
        if unsupported:
            raise ValidationError("Unsupported public projection fields.")
        if fields and locked.publication_status != "DRAFT":
            raise ValidationError("Public content can only be edited in DRAFT status.")
        _validate_structured_content(fields)
        for field_name, value in fields.items():
            setattr(locked, field_name, value)
        if fields:
            locked.save(update_fields=[*fields, "updated_at"])
            _audit(
                actor=actor,
                projection=locked,
                action="public_product.updated",
                old_status=locked.publication_status,
                new_status=locked.publication_status,
            )
        if target_status and target_status != locked.publication_status:
            return self.transition(locked, target_status, actor=actor)
        return locked

    @transaction.atomic
    def transition(self, projection, target_status, *, actor):
        locked = self.list_all().select_for_update().get(pk=projection.pk)
        old_status = locked.publication_status
        if target_status not in ALLOWED_TRANSITIONS.get(old_status, set()):
            raise ValidationError(
                f"Invalid publication transition: {old_status} -> {target_status}."
            )
        if target_status == "PUBLISHED":
            _validate_publishable(locked)
            locked.published_at = timezone.now()
        elif target_status == "DRAFT":
            locked.published_at = None
        locked.publication_status = target_status
        locked.save(update_fields=["publication_status", "published_at", "updated_at"])
        _audit(
            actor=actor,
            projection=locked,
            action=TRANSITION_AUDIT_ACTIONS[(old_status, target_status)],
            old_status=old_status,
            new_status=target_status,
        )
        return locked


