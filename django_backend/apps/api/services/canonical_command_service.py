"""Atomic Phase 4B master-data, RFQ, review, and document commands."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
import zipfile
from io import BytesIO
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import IntegrityError, models, transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.api.canonical_contract import CanonicalConflict
from apps.api.canonical_permissions import (
    CANONICAL_COMMAND_ROLE_MATRIX,
    has_exact_permission,
)
from apps.business_core.business_numbers import allocate_business_number
from apps.business_core.models import (
    BusinessCustomer,
    BusinessMaterial,
    BusinessProduct,
)
from apps.foundation.models import FoundationUser
from apps.knowledge.services.upload_security import MalwareScanner
from apps.sales.models import (
    SalesRfq,
    SalesRfqDocument,
    SalesRfqLine,
    SalesTechnicalReview,
)
from apps.transaction_domain.models import AuditEvent


MAX_COMMAND_ATTEMPTS = 3
IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
SAFE_STORAGE_KEY = re.compile(r"^rfq_documents/[0-9]+/[0-9a-f]{32}\.[a-z0-9]+$")
EDITABLE_HEADER_FIELDS = {
    "project_name",
    "notes",
    "quote_due_at",
    "required_delivery_date",
    "assigned_to_id",
}
LINE_FIELDS = {
    "part_id",
    "material_id",
    "description",
    "quantity",
    "unit",
    "required_delivery_date",
    "tolerance",
    "technical_notes",
    "drawing_required",
}


def _require_exact(actor, permission_code, *, roles=None, require_view=True):
    """Enforce exact role and exact permission rows without wildcard fallback."""
    role_name = getattr(getattr(actor, "role", None), "name", None)
    allowed = roles or CANONICAL_COMMAND_ROLE_MATRIX.get(permission_code, frozenset())
    if actor is None or not actor.is_active or role_name not in allowed:
        raise PermissionDenied(f"Missing canonical permission: {permission_code}")
    if not has_exact_permission(actor, permission_code):
        raise PermissionDenied(f"Missing canonical permission: {permission_code}")
    if require_view:
        view_code = f"{permission_code.split(':', 1)[0]}:view"
        if not has_exact_permission(actor, view_code):
            raise PermissionDenied(f"Missing canonical permission: {view_code}")


def _require_mvp(record, label):
    if record.data_contract != "MVP_V1":
        raise PermissionDenied(f"Legacy {label} records cannot use canonical commands.")


def _actor_identity(actor):
    return f"user:{actor.pk}", actor.full_name or actor.email


def _audit(
    *, actor, action, entity_type, entity_id, old_status="", new_status="",
    reason="", metadata=None,
):
    actor_ref, actor_display = _actor_identity(actor)
    return AuditEvent.objects.create(
        actor_ref=actor_ref,
        actor_display=actor_display,
        actor_user=actor,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        old_status=old_status,
        new_status=new_status,
        reason=reason,
        metadata=metadata or {},
    )


def _validate_customer_contact(*, status, email, phone):
    if status == "ACTIVE" and not (str(email).strip() or str(phone).strip()):
        raise ValidationError(
            {"contact": "An active customer requires an email address or phone number."}
        )


def _active_material(material_id):
    if material_id is None:
        return None
    material = BusinessMaterial.objects.get(pk=material_id)
    if material.data_contract != "MVP_V1" or not material.is_active:
        raise ValidationError({"default_material_id": "Material must be an active canonical record."})
    return material


def _active_part(part_id):
    if part_id is None:
        return None
    part = BusinessProduct.objects.get(pk=part_id)
    if part.data_contract != "MVP_V1" or not part.is_active:
        raise ValidationError({"part_id": "Part must be an active canonical record."})
    return part


def _create_with_number(namespace, builder):
    last_error = None
    for _attempt in range(MAX_COMMAND_ATTEMPTS):
        try:
            with transaction.atomic():
                code = allocate_business_number(namespace)
                return builder(code)
        except IntegrityError as exc:
            last_error = exc
    raise CanonicalConflict(
        f"Unable to allocate a unique {namespace} business number.",
        code="business_number_conflict",
    ) from last_error


class MasterDataCommandService:
    """Canonical Customer, Part, and Material command boundary."""

    @staticmethod
    def create_customer(actor, data):
        _require_exact(actor, "customer:create")
        _validate_customer_contact(
            status=data["status"], email=data.get("email", ""), phone=data.get("phone", "")
        )

        def builder(code):
            customer = BusinessCustomer(
                data_contract="MVP_V1",
                customer_code=code,
                company_name=data["company_name"].strip(),
                contact_name=data.get("contact_name", "").strip(),
                email=data.get("email", ""),
                phone=data.get("phone", ""),
                country=data.get("country", "Vietnam").strip(),
                status=data.get("status", "ACTIVE"),
                notes=data.get("notes", ""),
                created_by=actor,
                updated_by=actor,
            )
            customer.full_clean(
                exclude=["contact_name"],
                validate_unique=False,
                validate_constraints=False,
            )
            customer.save(force_insert=True)
            _audit(
                actor=actor,
                action="customer.created",
                entity_type="customer",
                entity_id=customer.pk,
                new_status=customer.status,
                metadata={"customer_code": customer.customer_code},
            )
            return customer

        return _create_with_number("CUS", builder)

    @staticmethod
    @transaction.atomic
    def update_customer(actor, customer_id, data):
        _require_exact(actor, "customer:change")
        customer = BusinessCustomer.objects.select_for_update().get(pk=customer_id)
        _require_mvp(customer, "customer")
        old_status = customer.status
        for field, value in data.items():
            setattr(customer, field, value.strip() if isinstance(value, str) else value)
        _validate_customer_contact(
            status=customer.status, email=customer.email, phone=customer.phone
        )
        customer.updated_by = actor
        customer.full_clean(exclude=["contact_name"])
        fields = sorted(data)
        customer.save(update_fields=[*fields, "updated_by", "updated_at"])
        _audit(
            actor=actor,
            action="customer.updated",
            entity_type="customer",
            entity_id=customer.pk,
            old_status=old_status,
            new_status=customer.status,
            metadata={"changed_fields": fields},
        )
        return customer

    @staticmethod
    @transaction.atomic
    def archive_customer(actor, customer_id):
        _require_exact(actor, "customer:archive")
        customer = BusinessCustomer.objects.select_for_update().get(pk=customer_id)
        _require_mvp(customer, "customer")
        if customer.status == "INACTIVE":
            raise CanonicalConflict("Customer is already inactive.", code="invalid_state")
        old_status = customer.status
        customer.status = "INACTIVE"
        customer.archived_at = timezone.now()
        customer.updated_by = actor
        customer.full_clean(exclude=["contact_name"])
        customer.save(update_fields=["status", "archived_at", "updated_by", "updated_at"])
        _audit(
            actor=actor,
            action="customer.archived",
            entity_type="customer",
            entity_id=customer.pk,
            old_status=old_status,
            new_status="INACTIVE",
        )
        return customer

    @staticmethod
    def create_part(actor, data):
        _require_exact(actor, "part:manage")

        def builder(code):
            material = _active_material(data.get("default_material_id"))
            part = BusinessProduct(
                data_contract="MVP_V1",
                part_code=code,
                name=data["name"].strip(),
                slug=slugify(f"{code}-{data['name']}")[:240],
                revision=data["revision"].strip(),
                unit=data["unit"],
                default_material=material,
                tolerance=data.get("tolerance", "").strip(),
                technical_requirements=data.get("technical_requirements", "").strip(),
                is_active=True,
                created_by=actor,
                updated_by=actor,
            )
            part.full_clean(validate_unique=False, validate_constraints=False)
            part.save(force_insert=True)
            return part

        return _create_with_number("PART", builder)

    @staticmethod
    @transaction.atomic
    def update_part(actor, part_id, data):
        _require_exact(actor, "part:manage")
        part = BusinessProduct.objects.select_for_update().get(pk=part_id)
        _require_mvp(part, "part")
        if not part.is_active:
            raise CanonicalConflict("Archived parts cannot be edited.", code="invalid_state")
        values = dict(data)
        if "default_material_id" in values:
            part.default_material = _active_material(values.pop("default_material_id"))
        for field, value in values.items():
            setattr(part, field, value.strip() if isinstance(value, str) else value)
        part.updated_by = actor
        part.full_clean()
        part.save()
        return part

    @staticmethod
    @transaction.atomic
    def archive_part(actor, part_id):
        _require_exact(actor, "part:archive")
        part = BusinessProduct.objects.select_for_update().get(pk=part_id)
        _require_mvp(part, "part")
        if not part.is_active:
            raise CanonicalConflict("Part is already archived.", code="invalid_state")
        part.is_active = False
        part.archived_at = timezone.now()
        part.updated_by = actor
        part.save(update_fields=["is_active", "archived_at", "updated_by", "updated_at"])
        return part

    @staticmethod
    def create_material(actor, data):
        _require_exact(actor, "material:manage")

        def builder(code):
            material = BusinessMaterial(
                data_contract="MVP_V1",
                material_code=code,
                name=data["name"].strip(),
                standard=data.get("standard", "").strip(),
                grade=data.get("grade", "").strip(),
                description=data.get("description", "").strip(),
                is_active=data.get("is_active", True),
                created_by=actor,
                updated_by=actor,
            )
            material.full_clean(validate_unique=False, validate_constraints=False)
            material.save(force_insert=True)
            return material

        return _create_with_number("MAT", builder)

    @staticmethod
    @transaction.atomic
    def update_material(actor, material_id, data):
        _require_exact(actor, "material:manage")
        material = BusinessMaterial.objects.select_for_update().get(pk=material_id)
        _require_mvp(material, "material")
        if not material.is_active:
            raise CanonicalConflict("Archived materials cannot be edited.", code="invalid_state")
        for field, value in data.items():
            setattr(material, field, value.strip() if isinstance(value, str) else value)
        material.updated_by = actor
        material.full_clean()
        material.save()
        return material

    @staticmethod
    @transaction.atomic
    def archive_material(actor, material_id):
        _require_exact(actor, "material:archive")
        material = BusinessMaterial.objects.select_for_update().get(pk=material_id)
        _require_mvp(material, "material")
        if not material.is_active:
            raise CanonicalConflict("Material is already archived.", code="invalid_state")
        material.is_active = False
        material.updated_by = actor
        material.save(update_fields=["is_active", "updated_by", "updated_at"])
        return material


def _json_safe(value):
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _request_hash(actor, data):
    payload = {"actor_id": actor.pk, "request": _json_safe(data)}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_idempotency_key(value):
    key = str(value or "").strip()
    if not IDEMPOTENCY_PATTERN.fullmatch(key):
        raise ValidationError(
            {"idempotency_key": "Idempotency-Key must contain 1-64 safe characters."}
        )
    return key


def _rfq_dates(*, quote_due_at, required_delivery_date, earliest=None, strict_due=False):
    today = earliest or timezone.localdate()
    if required_delivery_date < today:
        raise ValidationError(
            {"required_delivery_date": "Required delivery cannot be in the past."}
        )
    if quote_due_at > required_delivery_date:
        raise ValidationError({"quote_due_at": "Quote due date cannot follow delivery."})
    if strict_due and quote_due_at <= timezone.localdate():
        raise ValidationError({"quote_due_at": "Quote due date must be after submission."})


def _resolve_assignee(actor, assigned_to_id):
    role_name = actor.role.name
    if role_name == "Sales":
        if assigned_to_id not in (None, actor.pk):
            raise PermissionDenied("Sales cannot assign an RFQ to another user.")
        return actor
    if assigned_to_id is None:
        return actor
    assignee = FoundationUser.objects.select_related("role").get(pk=assigned_to_id)
    if not assignee.is_active or assignee.role.name not in {"Admin", "Sales"}:
        raise ValidationError({"assigned_to_id": "Assignee must be an active Admin or Sales user."})
    return assignee


def _require_rfq_owner(actor, rfq):
    if actor.role.name == "Sales" and actor.pk not in {rfq.created_by_id, rfq.assigned_to_id}:
        raise PermissionDenied("Sales may mutate only owned RFQs.")


def _requested_fields(rfq):
    review = rfq.technical_reviews.filter(decision="NEEDS_INFORMATION").order_by(
        "-created_at", "-id"
    ).first()
    return set(review.requested_fields if review else [])


def _require_editable(rfq, actor, category, changed_fields=None):
    _require_mvp(rfq, "RFQ")
    _require_rfq_owner(actor, rfq)
    if rfq.status == "DRAFT":
        return
    if rfq.status != "NEEDS_INFORMATION":
        raise CanonicalConflict("RFQ content is locked in its current state.", code="invalid_state")
    requested = _requested_fields(rfq)
    if category in {"lines", "documents"}:
        if category not in requested:
            raise PermissionDenied(f"{category.title()} were not requested for correction.")
        return
    denied = sorted(set(changed_fields or ()) - requested)
    if denied:
        raise PermissionDenied("Only specifically requested RFQ fields may be corrected.")


def _line_values(data):
    values = {key: value for key, value in data.items() if key in LINE_FIELDS}
    if "part_id" in values:
        _active_part(values["part_id"])
    if "material_id" in values:
        _active_material(values["material_id"])
    return values


def _require_valid_submission(rfq):
    earliest = timezone.localdate(rfq.created_at)
    _rfq_dates(
        quote_due_at=rfq.quote_due_at,
        required_delivery_date=rfq.required_delivery_date,
        earliest=earliest,
        strict_due=True,
    )
    if rfq.customer.data_contract != "MVP_V1" or rfq.customer.status != "ACTIVE":
        raise ValidationError({"customer": "RFQ requires an active canonical customer."})
    lines = list(rfq.lines.select_related("part", "material").order_by("line_number"))
    if not lines:
        raise ValidationError({"lines": "At least one valid RFQ line is required."})
    for line in lines:
        if line.quantity <= 0 or line.unit not in {"PCS", "KG", "M", "MM"}:
            raise ValidationError({"lines": f"Line {line.line_number} has invalid quantity or unit."})
        if not line.description.strip() and not (
            line.part_id and line.part.data_contract == "MVP_V1" and line.part.part_code
        ):
            raise ValidationError({"lines": f"Line {line.line_number} requires a part description or code."})
        if line.required_delivery_date < earliest:
            raise ValidationError({"lines": f"Line {line.line_number} has an invalid delivery date."})
        if not line.tolerance.strip() or not line.technical_notes.strip():
            raise ValidationError({"lines": f"Line {line.line_number} lacks required technical information."})
        if line.drawing_required and not rfq.documents.filter(
            rfq_line=line, document_revision__gt=""
        ).exists():
            raise ValidationError({"lines": f"Line {line.line_number} requires drawing evidence."})
    return lines


class RfqCommandService:
    """Canonical RFQ aggregate and technical-review command boundary."""

    @staticmethod
    def create(actor, data, idempotency_key):
        _require_exact(actor, "rfq:create")
        key = _validate_idempotency_key(idempotency_key)
        payload = dict(data)
        assignee = _resolve_assignee(actor, payload.get("assigned_to_id"))
        payload["assigned_to_id"] = assignee.pk
        digest = _request_hash(actor, payload)
        last_error = None
        for _attempt in range(MAX_COMMAND_ATTEMPTS):
            try:
                with transaction.atomic():
                    existing = SalesRfq.objects.select_for_update().filter(
                        idempotency_key=key
                    ).first()
                    if existing:
                        if existing.request_hash != digest:
                            raise CanonicalConflict(
                                "Idempotency key was already used for a different request.",
                                code="idempotency_conflict",
                            )
                        return existing, False
                    customer = BusinessCustomer.objects.select_for_update().get(
                        pk=payload["customer_id"]
                    )
                    if customer.data_contract != "MVP_V1" or customer.status != "ACTIVE":
                        raise ValidationError({"customer_id": "Customer must be active and canonical."})
                    _rfq_dates(
                        quote_due_at=payload["quote_due_at"],
                        required_delivery_date=payload["required_delivery_date"],
                    )
                    rfq = SalesRfq(
                        data_contract="MVP_V1",
                        rfq_number=allocate_business_number("RFQ"),
                        idempotency_key=key,
                        request_hash=digest,
                        customer=customer,
                        status="DRAFT",
                        project_name=payload.get("project_name", "").strip(),
                        notes=payload.get("notes", "").strip(),
                        quote_due_at=payload["quote_due_at"],
                        required_delivery_date=payload["required_delivery_date"],
                        assigned_to=assignee,
                        created_by=actor,
                        updated_by=actor,
                    )
                    rfq.full_clean(validate_unique=False, validate_constraints=False)
                    rfq.save(force_insert=True)
                    _audit(
                        actor=actor,
                        action="rfq.created",
                        entity_type="rfq",
                        entity_id=rfq.pk,
                        new_status="DRAFT",
                        metadata={"rfq_number": rfq.rfq_number},
                    )
                    return rfq, True
            except IntegrityError as exc:
                last_error = exc
                existing = SalesRfq.objects.filter(idempotency_key=key).first()
                if existing:
                    if existing.request_hash == digest:
                        return existing, False
                    raise CanonicalConflict(
                        "Idempotency key was already used for a different request.",
                        code="idempotency_conflict",
                    ) from exc
        raise CanonicalConflict(
            "Unable to allocate a unique RFQ number.", code="business_number_conflict"
        ) from last_error

    @staticmethod
    @transaction.atomic
    def update(actor, rfq_id, data):
        _require_exact(actor, "rfq:change")
        rfq = SalesRfq.objects.select_for_update().select_related("customer").get(pk=rfq_id)
        _require_editable(rfq, actor, "header", data)
        values = dict(data)
        if "assigned_to_id" in values:
            rfq.assigned_to = _resolve_assignee(actor, values.pop("assigned_to_id"))
        for field, value in values.items():
            setattr(rfq, field, value.strip() if isinstance(value, str) else value)
        _rfq_dates(
            quote_due_at=rfq.quote_due_at,
            required_delivery_date=rfq.required_delivery_date,
            earliest=timezone.localdate(rfq.created_at),
        )
        rfq.updated_by = actor
        rfq.full_clean()
        changed = sorted(data)
        rfq.save()
        _audit(
            actor=actor,
            action="rfq.updated",
            entity_type="rfq",
            entity_id=rfq.pk,
            old_status=rfq.status,
            new_status=rfq.status,
            metadata={"changed_fields": changed},
        )
        return rfq

    @staticmethod
    @transaction.atomic
    def add_line(actor, rfq_id, data):
        _require_exact(actor, "rfq:change")
        rfq = SalesRfq.objects.select_for_update().get(pk=rfq_id)
        _require_editable(rfq, actor, "lines")
        next_number = (rfq.lines.aggregate(value=models.Max("line_number"))["value"] or 0) + 1
        line = SalesRfqLine(rfq=rfq, line_number=next_number, **_line_values(data))
        line.full_clean()
        line.save(force_insert=True)
        _audit(
            actor=actor,
            action="rfq.updated",
            entity_type="rfq",
            entity_id=rfq.pk,
            old_status=rfq.status,
            new_status=rfq.status,
            metadata={"operation": "line_added", "line_id": line.pk},
        )
        return line

    @staticmethod
    @transaction.atomic
    def update_line(actor, rfq_id, line_id, data):
        _require_exact(actor, "rfq:change")
        rfq = SalesRfq.objects.select_for_update().get(pk=rfq_id)
        _require_editable(rfq, actor, "lines")
        line = SalesRfqLine.objects.select_for_update().get(pk=line_id, rfq=rfq)
        for field, value in _line_values(data).items():
            setattr(line, field, value)
        line.full_clean()
        line.save()
        _audit(
            actor=actor,
            action="rfq.updated",
            entity_type="rfq",
            entity_id=rfq.pk,
            old_status=rfq.status,
            new_status=rfq.status,
            metadata={"operation": "line_updated", "line_id": line.pk},
        )
        return line

    @staticmethod
    @transaction.atomic
    def remove_line(actor, rfq_id, line_id):
        _require_exact(actor, "rfq:change")
        rfq = SalesRfq.objects.select_for_update().get(pk=rfq_id)
        _require_editable(rfq, actor, "lines")
        line = SalesRfqLine.objects.select_for_update().get(pk=line_id, rfq=rfq)
        if line.documents.exists():
            raise CanonicalConflict(
                "RFQ lines with versioned document evidence cannot be removed.",
                code="document_evidence_conflict",
            )
        line.delete()
        _audit(
            actor=actor,
            action="rfq.updated",
            entity_type="rfq",
            entity_id=rfq.pk,
            old_status=rfq.status,
            new_status=rfq.status,
            metadata={"operation": "line_removed", "line_id": line_id},
        )

    @staticmethod
    @transaction.atomic
    def submit(actor, rfq_id):
        _require_exact(actor, "rfq:submit")
        rfq = SalesRfq.objects.select_for_update().select_related("customer").get(pk=rfq_id)
        _require_mvp(rfq, "RFQ")
        _require_rfq_owner(actor, rfq)
        if rfq.status != "DRAFT":
            raise CanonicalConflict("Only DRAFT RFQs may be submitted.", code="invalid_state")
        _require_valid_submission(rfq)
        old_status = rfq.status
        rfq.status = "SUBMITTED"
        rfq.updated_by = actor
        rfq.save(update_fields=["status", "updated_by", "updated_at"])
        _audit(
            actor=actor, action="rfq.submitted", entity_type="rfq", entity_id=rfq.pk,
            old_status=old_status, new_status="SUBMITTED",
        )
        return rfq

    @staticmethod
    @transaction.atomic
    def archive(actor, rfq_id, reason):
        _require_exact(actor, "rfq:archive")
        rfq = SalesRfq.objects.select_for_update().get(pk=rfq_id)
        _require_mvp(rfq, "RFQ")
        _require_rfq_owner(actor, rfq)
        if rfq.status != "DRAFT":
            raise CanonicalConflict("Only DRAFT RFQs may be archived.", code="invalid_state")
        old_status = rfq.status
        rfq.status = "CLOSED"
        rfq.closure_reason = reason.strip()
        rfq.updated_by = actor
        rfq.full_clean()
        rfq.save(update_fields=["status", "closure_reason", "updated_by", "updated_at"])
        _audit(
            actor=actor, action="rfq.closed", entity_type="rfq", entity_id=rfq.pk,
            old_status=old_status, new_status="CLOSED", reason=rfq.closure_reason,
        )
        return rfq

    @staticmethod
    @transaction.atomic
    def resubmit(actor, rfq_id):
        _require_exact(actor, "rfq:submit")
        rfq = SalesRfq.objects.select_for_update().select_related("customer").get(pk=rfq_id)
        _require_mvp(rfq, "RFQ")
        _require_rfq_owner(actor, rfq)
        if rfq.status != "NEEDS_INFORMATION":
            raise CanonicalConflict(
                "Only NEEDS_INFORMATION RFQs may be resubmitted.", code="invalid_state"
            )
        if not _requested_fields(rfq):
            raise ValidationError({"review": "Requested correction evidence is missing."})
        _require_valid_submission(rfq)
        rfq.status = "SUBMITTED"
        rfq.updated_by = actor
        rfq.save(update_fields=["status", "updated_by", "updated_at"])
        _audit(
            actor=actor, action="rfq.resubmitted", entity_type="rfq", entity_id=rfq.pk,
            old_status="NEEDS_INFORMATION", new_status="SUBMITTED",
        )
        return rfq

    @staticmethod
    @transaction.atomic
    def start_review(actor, rfq_id):
        _require_exact(actor, "rfq:review")
        rfq = SalesRfq.objects.select_for_update().get(pk=rfq_id)
        _require_mvp(rfq, "RFQ")
        if rfq.status != "SUBMITTED":
            raise CanonicalConflict("Only SUBMITTED RFQs may enter review.", code="invalid_state")
        rfq.status = "UNDER_REVIEW"
        rfq.updated_by = actor
        rfq.save(update_fields=["status", "updated_by", "updated_at"])
        review = SalesTechnicalReview.objects.create(rfq=rfq, reviewer=actor, decision="STARTED")
        _audit(
            actor=actor, action="rfq.technical_review_started", entity_type="rfq",
            entity_id=rfq.pk, old_status="SUBMITTED", new_status="UNDER_REVIEW",
        )
        return rfq, review

    @staticmethod
    @transaction.atomic
    def request_information(actor, rfq_id, data):
        _require_exact(actor, "rfq:review")
        rfq = SalesRfq.objects.select_for_update().get(pk=rfq_id)
        _require_mvp(rfq, "RFQ")
        if rfq.status != "UNDER_REVIEW":
            raise CanonicalConflict("RFQ is not under review.", code="invalid_state")
        review = SalesTechnicalReview.objects.create(
            rfq=rfq,
            reviewer=actor,
            decision="NEEDS_INFORMATION",
            reason=data["reason"].strip(),
            notes=data.get("notes", "").strip(),
            requested_fields=data["requested_fields"],
        )
        rfq.status = "NEEDS_INFORMATION"
        rfq.updated_by = actor
        rfq.save(update_fields=["status", "updated_by", "updated_at"])
        _audit(
            actor=actor, action="rfq.information_requested", entity_type="rfq",
            entity_id=rfq.pk, old_status="UNDER_REVIEW", new_status="NEEDS_INFORMATION",
            reason=review.reason, metadata={"requested_fields": review.requested_fields},
        )
        return rfq, review

    @staticmethod
    @transaction.atomic
    def complete_review(actor, rfq_id, data):
        _require_exact(actor, "rfq:review")
        rfq = SalesRfq.objects.select_for_update().get(pk=rfq_id)
        _require_mvp(rfq, "RFQ")
        if rfq.status != "UNDER_REVIEW":
            raise CanonicalConflict("RFQ is not under review.", code="invalid_state")
        lines = list(rfq.lines.select_related("part", "material").order_by("line_number"))
        if not lines:
            raise ValidationError({"lines": "Technical review requires RFQ lines."})
        actual_ids = {line.pk for line in lines}
        feasible_ids = set(data["feasible_line_ids"])
        if feasible_ids != actual_ids:
            raise ValidationError({"feasible_line_ids": "Every RFQ line must be marked feasible."})
        no_drawing_ids = set(data.get("drawing_not_required_line_ids", []))
        if not no_drawing_ids.issubset(actual_ids):
            raise ValidationError({"drawing_not_required_line_ids": "Unknown RFQ line."})
        evidence = []
        for line in lines:
            if not (line.material_id or (line.part_id and line.part.default_material_id)):
                raise ValidationError({"lines": f"Line {line.line_number} requires material evidence."})
            if not line.tolerance.strip() or not line.technical_notes.strip():
                raise ValidationError({"lines": f"Line {line.line_number} lacks technical evidence."})
            if line.drawing_required:
                if not rfq.documents.filter(rfq_line=line, document_revision__gt="").exists():
                    raise ValidationError({"lines": f"Line {line.line_number} requires a drawing revision."})
            elif line.pk not in no_drawing_ids:
                raise ValidationError(
                    {"drawing_not_required_line_ids": f"Line {line.line_number} needs reviewer confirmation."}
                )
            evidence.append(f"feasible_line:{line.pk}")
            if line.pk in no_drawing_ids:
                evidence.append(f"drawing_not_required_line:{line.pk}")
        review = SalesTechnicalReview.objects.create(
            rfq=rfq,
            reviewer=actor,
            decision="READY_TO_QUOTE",
            notes=data.get("notes", "").strip(),
            requested_fields=evidence,
        )
        rfq.status = "READY_TO_QUOTE"
        rfq.updated_by = actor
        rfq.save(update_fields=["status", "updated_by", "updated_at"])
        _audit(
            actor=actor, action="rfq.review_completed", entity_type="rfq",
            entity_id=rfq.pk, old_status="UNDER_REVIEW", new_status="READY_TO_QUOTE",
            metadata={"line_count": len(lines)},
        )
        return rfq, review

    @staticmethod
    @transaction.atomic
    def decline(actor, rfq_id, reason):
        _require_exact(actor, "rfq:review")
        rfq = SalesRfq.objects.select_for_update().get(pk=rfq_id)
        _require_mvp(rfq, "RFQ")
        if rfq.status != "UNDER_REVIEW":
            raise CanonicalConflict("RFQ is not under review.", code="invalid_state")
        review = SalesTechnicalReview.objects.create(
            rfq=rfq, reviewer=actor, decision="DECLINED", reason=reason.strip()
        )
        rfq.status = "DECLINED"
        rfq.updated_by = actor
        rfq.save(update_fields=["status", "updated_by", "updated_at"])
        _audit(
            actor=actor, action="rfq.declined", entity_type="rfq", entity_id=rfq.pk,
            old_status="UNDER_REVIEW", new_status="DECLINED", reason=review.reason,
        )
        return rfq, review

    @staticmethod
    @transaction.atomic
    def acknowledge_declined(actor, rfq_id, reason):
        role_name = getattr(getattr(actor, "role", None), "name", None)
        if role_name == "Manager":
            _require_exact(actor, "rfq:review")
        elif role_name == "Admin":
            _require_exact(actor, "rfq:archive")
        else:
            raise PermissionDenied("Only Manager or Admin may acknowledge a declined RFQ.")
        rfq = SalesRfq.objects.select_for_update().get(pk=rfq_id)
        _require_mvp(rfq, "RFQ")
        if rfq.status != "DECLINED":
            raise CanonicalConflict("Only DECLINED RFQs may be closed.", code="invalid_state")
        rfq.status = "CLOSED"
        rfq.closure_reason = reason.strip()
        rfq.updated_by = actor
        rfq.full_clean()
        rfq.save(update_fields=["status", "closure_reason", "updated_by", "updated_at"])
        _audit(
            actor=actor, action="rfq.closed", entity_type="rfq", entity_id=rfq.pk,
            old_status="DECLINED", new_status="CLOSED", reason=rfq.closure_reason,
        )
        return rfq


class RfqDocumentSecurityService:
    """Bounded RFQ document validation, storage, versioning, and retrieval."""

    MIME_BY_EXTENSION = {
        ".pdf": {"application/pdf"},
        ".step": {"application/step", "model/step"},
        ".stp": {"application/step", "model/step"},
        ".dxf": {"application/dxf", "image/vnd.dxf"},
        ".xlsx": {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        },
    }

    def __init__(self, scanner=None):
        self.scanner = scanner or MalwareScanner()

    def validate(self, uploaded_file):
        raw_name = str(getattr(uploaded_file, "name", "") or "").replace("\\", "/")
        path = PurePosixPath(raw_name)
        if not raw_name or path.is_absolute() or ".." in path.parts:
            raise ValidationError({"file": "A safe filename is required."})
        filename = path.name
        extension = Path(filename).suffix.casefold()
        if extension not in self.MIME_BY_EXTENSION:
            raise ValidationError({"file": "Unsupported RFQ document extension."})
        declared_mime = str(getattr(uploaded_file, "content_type", "") or "").casefold()
        if declared_mime not in self.MIME_BY_EXTENSION[extension]:
            raise ValidationError({"file": "Declared MIME type does not match the extension."})
        max_bytes = int(
            getattr(settings, "RFQ_DOCUMENT_MAX_BYTES", getattr(settings, "UPLOAD_MAX_BYTES", 10 * 1024 * 1024))
        )
        declared_size = int(getattr(uploaded_file, "size", 0) or 0)
        if declared_size > max_bytes:
            raise ValidationError({"file": "RFQ document exceeds the configured size limit."})
        content = uploaded_file.read(max_bytes + 1)
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        if not content:
            raise ValidationError({"file": "RFQ document is empty."})
        if len(content) > max_bytes:
            raise ValidationError({"file": "RFQ document exceeds the configured size limit."})
        self._validate_signature(extension, content)
        self.scanner.scan(filename, content)
        return {
            "filename": filename,
            "extension": extension,
            "mime_type": declared_mime,
            "content": content,
            "size_bytes": len(content),
            "checksum_sha256": hashlib.sha256(content).hexdigest(),
        }

    def _validate_signature(self, extension, content):
        if extension == ".pdf" and not content.startswith(b"%PDF-"):
            raise ValidationError({"file": "PDF signature is invalid."})
        if extension in {".step", ".stp"}:
            if not content.lstrip().upper().startswith(b"ISO-10303-21;"):
                raise ValidationError({"file": "STEP signature is invalid."})
        if extension == ".dxf":
            prefix = content[:4096].decode("ascii", errors="ignore").replace("\r", "")
            tokens = [item.strip().upper() for item in prefix.split("\n") if item.strip()]
            if len(tokens) < 2 or tokens[0:2] != ["0", "SECTION"]:
                raise ValidationError({"file": "DXF signature is invalid."})
        if extension == ".xlsx":
            try:
                archive = zipfile.ZipFile(BytesIO(content))
                infos = archive.infolist()
            except zipfile.BadZipFile as exc:
                raise ValidationError({"file": "XLSX archive is invalid."}) from exc
            if len(infos) > int(getattr(settings, "UPLOAD_ARCHIVE_MAX_MEMBERS", 500)):
                raise ValidationError({"file": "XLSX archive has too many members."})
            names = set()
            total = 0
            compressed = 0
            for info in infos:
                member = PurePosixPath(info.filename.replace("\\", "/"))
                if info.flag_bits & 0x1 or member.is_absolute() or ".." in member.parts:
                    raise ValidationError({"file": "XLSX archive contains an unsafe member."})
                names.add(info.filename)
                total += info.file_size
                compressed += info.compress_size
            max_uncompressed = int(
                getattr(settings, "UPLOAD_ARCHIVE_MAX_UNCOMPRESSED_BYTES", 50 * 1024 * 1024)
            )
            ratio = int(getattr(settings, "UPLOAD_ARCHIVE_MAX_RATIO", 100))
            if total > max_uncompressed or total / max(1, compressed) > ratio:
                raise ValidationError({"file": "XLSX archive expansion limit exceeded."})
            if not {"[Content_Types].xml", "xl/workbook.xml"}.issubset(names):
                raise ValidationError({"file": "XLSX workbook content is missing."})

    @staticmethod
    def _storage_key(rfq_id, extension):
        return f"rfq_documents/{rfq_id}/{uuid.uuid4().hex}{extension}"

    @staticmethod
    def _validate_storage_key(rfq_id, storage_key):
        normalized = str(storage_key or "").replace("\\", "/")
        path = PurePosixPath(normalized)
        expected_prefix = ("rfq_documents", str(rfq_id))
        if (
            not SAFE_STORAGE_KEY.fullmatch(normalized)
            or path.is_absolute()
            or ".." in path.parts
            or path.parts[:2] != expected_prefix
        ):
            raise CanonicalConflict("Private RFQ document is unavailable.", code="document_unavailable")
        if hasattr(default_storage, "path"):
            try:
                actual = Path(default_storage.path(normalized))
                root = Path(default_storage.location).resolve()
                resolved = actual.resolve()
                if root != resolved and root not in resolved.parents:
                    raise CanonicalConflict(
                        "Private RFQ document is unavailable.", code="document_unavailable"
                    )
                if actual.is_symlink():
                    raise CanonicalConflict(
                        "Private RFQ document is unavailable.", code="document_unavailable"
                    )
            except (NotImplementedError, AttributeError):
                pass
        return normalized

    def upload(self, actor, rfq_id, data, *, replaces_id=None):
        _require_exact(actor, "rfq:document_upload")
        processed = self.validate(data["file"])
        stored_key = None
        try:
            with transaction.atomic():
                rfq = SalesRfq.objects.select_for_update().get(pk=rfq_id)
                _require_editable(rfq, actor, "documents")
                line = None
                line_id = data.get("rfq_line_id")
                if line_id is not None:
                    line = SalesRfqLine.objects.get(pk=line_id, rfq=rfq)
                replaces = None
                group_id = uuid.uuid4()
                version = 1
                action = "rfq.document_uploaded"
                if replaces_id is not None:
                    requested = SalesRfqDocument.objects.get(pk=replaces_id, rfq=rfq)
                    replaces = SalesRfqDocument.objects.select_for_update().filter(
                        rfq=rfq, document_group_id=requested.document_group_id
                    ).order_by("-version", "-id").first()
                    group_id = replaces.document_group_id
                    version = replaces.version + 1
                    if line is None:
                        line = replaces.rfq_line
                    action = "rfq.document_versioned"
                storage_key = self._storage_key(rfq.pk, processed["extension"])
                stored_key = default_storage.save(
                    storage_key, ContentFile(processed["content"])
                )
                if stored_key != storage_key:
                    raise CanonicalConflict("Storage key collision.", code="storage_conflict")
                self._validate_storage_key(rfq.pk, stored_key)
                document = SalesRfqDocument(
                    rfq=rfq,
                    rfq_line=line,
                    document_group_id=group_id,
                    version=version,
                    original_filename=processed["filename"],
                    storage_key=stored_key,
                    mime_type=processed["mime_type"],
                    size_bytes=processed["size_bytes"],
                    checksum_sha256=processed["checksum_sha256"],
                    document_revision=data.get("document_revision", "").strip(),
                    replaces=replaces,
                    uploaded_by=actor,
                )
                document.full_clean()
                document.save(force_insert=True)
                _audit(
                    actor=actor,
                    action=action,
                    entity_type="rfq",
                    entity_id=rfq.pk,
                    old_status=rfq.status,
                    new_status=rfq.status,
                    metadata={
                        "document_id": document.pk,
                        "document_version": document.version,
                        "size_bytes": document.size_bytes,
                    },
                )
                return document
        except Exception:
            if stored_key and default_storage.exists(stored_key):
                default_storage.delete(stored_key)
            raise

    @staticmethod
    def open_for_download(actor, rfq_id, document_id):
        _require_exact(actor, "rfq:document_download")
        rfq = SalesRfq.objects.get(pk=rfq_id)
        _require_mvp(rfq, "RFQ")
        document = SalesRfqDocument.objects.get(pk=document_id, rfq=rfq)
        key = RfqDocumentSecurityService._validate_storage_key(rfq.pk, document.storage_key)
        if not default_storage.exists(key):
            raise CanonicalConflict("Private RFQ document is unavailable.", code="document_unavailable")
        return document, default_storage.open(key, "rb")
