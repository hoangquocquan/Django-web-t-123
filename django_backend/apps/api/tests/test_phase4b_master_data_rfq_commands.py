"""Focused Phase 4B canonical master-data and RFQ command tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier

import pytest
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.db.models.deletion import ProtectedError
from django.urls import resolve
from django.utils import timezone

from apps.api.services import canonical_command_service as command_module
from apps.api.services.canonical_command_service import (
    RfqCommandService,
    RfqDocumentSecurityService,
)
from apps.business_core.models import BusinessCustomer, BusinessMaterial, BusinessProduct
from apps.foundation.models import (
    FoundationAuthToken,
    FoundationPermission,
    FoundationRole,
    FoundationUser,
)
from apps.foundation.services import FoundationAuthService
from apps.sales.models import SalesRfq, SalesRfqDocument, SalesRfqLine, SalesTechnicalReview
from apps.transaction_domain.models import AuditEvent, TransactionOrder


ROLE_PERMISSIONS = {
    "Admin": {
        "customer:view", "customer:create", "customer:change", "customer:archive",
        "part:view", "part:manage", "part:archive",
        "material:view", "material:manage", "material:archive",
        "rfq:view", "rfq:create", "rfq:change", "rfq:archive", "rfq:submit",
        "rfq:document_upload", "rfq:document_download",
    },
    "Sales": {
        "customer:view", "customer:create", "customer:change", "customer:archive",
        "part:view", "material:view",
        "rfq:view", "rfq:create", "rfq:change", "rfq:archive", "rfq:submit",
        "rfq:document_upload", "rfq:document_download",
    },
    "Manager": {
        "customer:view", "part:view", "material:view", "rfq:view", "rfq:review",
        "rfq:document_download",
    },
}


def _permission(code):
    module, action = code.split(":", 1)
    permission, _created = FoundationPermission.objects.get_or_create(
        code=code,
        defaults={"module": module, "action": action, "description": "Phase 4B test"},
    )
    if (permission.module, permission.action) != (module, action):
        permission.module = module
        permission.action = action
        permission.save(update_fields=["module", "action"])
    return permission


def _user(role_name, suffix, permissions=(), active=True):
    role, _created = FoundationRole.objects.get_or_create(
        name=role_name, defaults={"description": f"Phase 4B {role_name}"}
    )
    for code in permissions:
        role.permissions.add(_permission(code))
    return FoundationUser.objects.create(
        email=f"{suffix}@phase4b.example",
        full_name=f"Phase 4B {suffix}",
        password_hash="test-only-not-a-secret",
        role=role,
        is_active=active,
    )


def _token(user, suffix):
    raw = f"phase4b-{suffix}-token"
    FoundationAuthToken.objects.create(
        user=user,
        token_hash=FoundationAuthService.hash_token(raw),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    return raw


def _headers(context, role):
    return {"HTTP_AUTHORIZATION": f"Bearer {context['tokens'][role]}"}


@pytest.fixture
def phase4b_context(db):
    users = {}
    tokens = {}
    for role_name, permissions in ROLE_PERMISSIONS.items():
        key = role_name.casefold()
        users[key] = _user(role_name, key, permissions)
        tokens[key] = _token(users[key], key)
    users["other_sales"] = _user("Sales", "other-sales", ROLE_PERMISSIONS["Sales"])
    tokens["other_sales"] = _token(users["other_sales"], "other-sales")
    users["inactive"] = _user("Sales", "inactive", ROLE_PERMISSIONS["Sales"], active=False)
    tokens["inactive"] = _token(users["inactive"], "inactive")
    users["wildcard"] = _user("Wildcard", "wildcard")
    wildcard, _created = FoundationPermission.objects.get_or_create(
        code="*:*",
        defaults={"module": "*", "action": "*", "description": "Legacy wildcard"},
    )
    users["wildcard"].role.permissions.add(wildcard)
    tokens["wildcard"] = _token(users["wildcard"], "wildcard")

    customer = BusinessCustomer.objects.create(
        data_contract="MVP_V1",
        customer_code="CUS-P4B-SEED",
        company_name="Phase 4B Customer",
        contact_name="Buyer",
        email="buyer@example.com",
        status="ACTIVE",
        created_by=users["sales"],
        updated_by=users["sales"],
    )
    material = BusinessMaterial.objects.create(
        data_contract="MVP_V1",
        material_code="MAT-P4B-SEED",
        name="SUS304",
        standard="JIS",
        grade="304",
        created_by=users["admin"],
    )
    part = BusinessProduct.objects.create(
        data_contract="MVP_V1",
        part_code="PART-P4B-SEED",
        name="Precision shaft",
        slug="phase4b-precision-shaft",
        revision="A",
        unit="PCS",
        default_material=material,
        tolerance="h6",
        technical_requirements="Turn and grind",
        created_by=users["admin"],
    )
    return {
        "users": users,
        "tokens": tokens,
        "customer": customer,
        "material": material,
        "part": part,
    }


@pytest.fixture
def rfq_storage(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    }
    settings.RFQ_DOCUMENT_MAX_BYTES = 1024
    storages._storages.clear()
    yield tmp_path
    storages._storages.clear()


def _rfq_payload(context, *, days=10):
    today = timezone.localdate()
    return {
        "customer_id": context["customer"].pk,
        "project_name": "Canonical RFQ",
        "notes": "Initial request",
        "quote_due_at": (today + timedelta(days=days)).isoformat(),
        "required_delivery_date": (today + timedelta(days=days + 20)).isoformat(),
    }


def _create_rfq(client, context, *, key="phase4b-rfq-key"):
    response = client.post(
        "/api/v1/canonical/rfqs/commands/create/",
        _rfq_payload(context),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY=key,
        **_headers(context, "sales"),
    )
    assert response.status_code == 201, response.json()
    return SalesRfq.objects.get(pk=response.json()["data"]["id"])


def _line_payload(context, *, drawing_required=False):
    return {
        "part_id": context["part"].pk,
        "material_id": context["material"].pk,
        "description": "Shaft per controlled drawing",
        "quantity": "2.5000",
        "unit": "PCS",
        "required_delivery_date": (timezone.localdate() + timedelta(days=30)).isoformat(),
        "tolerance": "h6",
        "technical_notes": "Surface finish Ra 0.8",
        "drawing_required": drawing_required,
    }


def _add_line(client, context, rfq, *, drawing_required=False):
    response = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/lines/commands/add/",
        _line_payload(context, drawing_required=drawing_required),
        content_type="application/json",
        **_headers(context, "sales"),
    )
    assert response.status_code == 201, response.json()
    return SalesRfqLine.objects.get(pk=response.json()["data"]["id"])


@pytest.mark.django_db
def test_customer_create_update_archive_rbac_validation_and_audit(client, phase4b_context):
    payload = {
        "company_name": "  New Buyer  ",
        "email": "BUYER@EXAMPLE.COM",
        "phone": "+81 (90) 1234-5678",
    }
    response = client.post(
        "/api/v1/canonical/customers/commands/create/",
        payload,
        content_type="application/json",
        **_headers(phase4b_context, "sales"),
    )
    assert response.status_code == 201
    customer = BusinessCustomer.objects.get(pk=response.json()["data"]["id"])
    assert customer.customer_code == "CUS-0001"
    assert customer.company_name == "New Buyer"
    assert customer.email == "buyer@example.com"
    assert customer.phone == "+819012345678"
    assert customer.data_contract == "MVP_V1"
    assert AuditEvent.objects.filter(action="customer.created", entity_id=str(customer.pk)).count() == 1

    update = client.post(
        f"/api/v1/canonical/customers/{customer.pk}/commands/update/",
        {"notes": "Approved account"},
        content_type="application/json",
        **_headers(phase4b_context, "sales"),
    )
    assert update.status_code == 200
    archive = client.post(
        f"/api/v1/canonical/customers/{customer.pk}/commands/archive/",
        {}, content_type="application/json", **_headers(phase4b_context, "sales")
    )
    assert archive.status_code == 200
    customer.refresh_from_db()
    assert customer.status == "INACTIVE" and customer.archived_at is not None
    assert set(AuditEvent.objects.filter(entity_type="customer", entity_id=str(customer.pk)).values_list("action", flat=True)) == {
        "customer.created", "customer.updated", "customer.archived"
    }

    denied = client.post(
        "/api/v1/canonical/customers/commands/create/",
        payload, content_type="application/json", **_headers(phase4b_context, "manager")
    )
    assert denied.status_code == 403
    invalid = client.post(
        "/api/v1/canonical/customers/commands/create/",
        {"company_name": "No Contact"},
        content_type="application/json",
        **_headers(phase4b_context, "sales"),
    )
    assert invalid.status_code == 400


@pytest.mark.django_db
def test_command_authentication_inactive_and_wildcard_fail_closed(client, phase4b_context):
    path = "/api/v1/canonical/customers/commands/create/"
    payload = {"company_name": "Blocked", "email": "blocked@example.com"}
    assert client.post(path, payload, content_type="application/json").status_code == 401
    assert client.post(path, payload, content_type="application/json", **_headers(phase4b_context, "inactive")).status_code == 401
    assert client.post(path, payload, content_type="application/json", **_headers(phase4b_context, "wildcard")).status_code == 403


@pytest.mark.django_db
def test_referenced_customer_hard_delete_is_database_protected(phase4b_context):
    today = timezone.localdate()
    SalesRfq.objects.create(
        rfq_number="RFQ-P4B-PROTECT",
        customer=phase4b_context["customer"],
        quote_due_at=today + timedelta(days=2),
        required_delivery_date=today + timedelta(days=10),
        created_by=phase4b_context["users"]["sales"],
    )
    with pytest.raises(ProtectedError):
        phase4b_context["customer"].delete()


@pytest.mark.django_db
def test_part_and_material_commands_are_admin_only_and_server_numbered(client, phase4b_context):
    material_response = client.post(
        "/api/v1/canonical/materials/commands/create/",
        {"name": "S45C", "standard": "JIS", "grade": "S45C"},
        content_type="application/json",
        **_headers(phase4b_context, "admin"),
    )
    assert material_response.status_code == 201
    material = BusinessMaterial.objects.get(pk=material_response.json()["data"]["id"])
    assert material.material_code == "MAT-0001"
    part_response = client.post(
        "/api/v1/canonical/parts/commands/create/",
        {
            "name": "Housing", "revision": "B", "unit": "PCS",
            "default_material_id": material.pk,
        },
        content_type="application/json",
        **_headers(phase4b_context, "admin"),
    )
    assert part_response.status_code == 201
    part = BusinessProduct.objects.get(pk=part_response.json()["data"]["id"])
    assert part.part_code == "PART-0001" and part.default_material_id == material.pk
    for role in ("sales", "manager"):
        denied = client.post(
            "/api/v1/canonical/materials/commands/create/",
            {"name": "Denied"}, content_type="application/json",
            **_headers(phase4b_context, role),
        )
        assert denied.status_code == 403
    assert client.post(
        f"/api/v1/canonical/parts/{part.pk}/commands/archive/",
        {}, content_type="application/json", **_headers(phase4b_context, "admin")
    ).status_code == 200
    assert client.post(
        f"/api/v1/canonical/materials/{material.pk}/commands/archive/",
        {}, content_type="application/json", **_headers(phase4b_context, "admin")
    ).status_code == 200


@pytest.mark.django_db
def test_duplicate_business_codes_are_rejected_by_constraints(phase4b_context):
    with pytest.raises(IntegrityError), transaction.atomic():
        BusinessCustomer.objects.create(
            data_contract="MVP_V1", customer_code="CUS-P4B-SEED",
            company_name="Duplicate", email="dupe@example.com", status="ACTIVE",
            created_by=phase4b_context["users"]["sales"],
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        BusinessMaterial.objects.create(
            material_code="MAT-P4B-SEED", name="Duplicate",
            created_by=phase4b_context["users"]["admin"],
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        BusinessProduct.objects.create(
            data_contract="MVP_V1", part_code="PART-P4B-SEED", name="Duplicate",
            slug="phase4b-duplicate", revision="A", unit="PCS",
            created_by=phase4b_context["users"]["admin"],
        )


@pytest.mark.django_db
def test_rfq_create_is_idempotent_and_hash_conflict_is_atomic(client, phase4b_context):
    first = _create_rfq(client, phase4b_context)
    second_response = client.post(
        "/api/v1/canonical/rfqs/commands/create/",
        _rfq_payload(phase4b_context), content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="phase4b-rfq-key", **_headers(phase4b_context, "sales"),
    )
    assert second_response.status_code == 200
    assert second_response.json()["data"]["id"] == first.pk
    assert SalesRfq.objects.count() == 1
    assert AuditEvent.objects.filter(action="rfq.created").count() == 1
    conflict_payload = _rfq_payload(phase4b_context)
    conflict_payload["project_name"] = "Different request"
    conflict = client.post(
        "/api/v1/canonical/rfqs/commands/create/",
        conflict_payload, content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="phase4b-rfq-key", **_headers(phase4b_context, "sales"),
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "idempotency_conflict"
    assert SalesRfq.objects.count() == 1


@pytest.mark.django_db
def test_rfq_ownership_draft_editing_and_locked_state(client, phase4b_context):
    rfq = _create_rfq(client, phase4b_context)
    denied = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/commands/update/",
        {"notes": "not mine"}, content_type="application/json",
        **_headers(phase4b_context, "other_sales"),
    )
    assert denied.status_code == 403
    allowed = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/commands/update/",
        {"notes": "owned update"}, content_type="application/json",
        **_headers(phase4b_context, "sales"),
    )
    assert allowed.status_code == 200
    rfq.status = "SUBMITTED"
    rfq.save(update_fields=["status"])
    locked = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/commands/update/",
        {"notes": "locked"}, content_type="application/json",
        **_headers(phase4b_context, "sales"),
    )
    assert locked.status_code == 409


@pytest.mark.django_db
def test_line_commands_validate_and_submit_failures_are_atomic(client, phase4b_context):
    rfq = _create_rfq(client, phase4b_context)
    before = AuditEvent.objects.count()
    no_lines = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/commands/submit/",
        {}, content_type="application/json", **_headers(phase4b_context, "sales")
    )
    assert no_lines.status_code == 400
    rfq.refresh_from_db()
    assert rfq.status == "DRAFT" and AuditEvent.objects.count() == before
    invalid_line = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/lines/commands/add/",
        {**_line_payload(phase4b_context), "quantity": "0"},
        content_type="application/json", **_headers(phase4b_context, "sales"),
    )
    assert invalid_line.status_code == 400
    line = _add_line(client, phase4b_context, rfq)
    update = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/lines/{line.pk}/commands/update/",
        {"quantity": "3.0000"}, content_type="application/json",
        **_headers(phase4b_context, "sales"),
    )
    assert update.status_code == 200
    submit = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/commands/submit/",
        {}, content_type="application/json", **_headers(phase4b_context, "sales")
    )
    assert submit.status_code == 200, submit.json()
    rfq.refresh_from_db()
    assert rfq.status == "SUBMITTED"
    remove_locked = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/lines/{line.pk}/commands/remove/",
        {}, content_type="application/json", **_headers(phase4b_context, "sales")
    )
    assert remove_locked.status_code == 409


@pytest.mark.django_db
def test_every_review_transition_needs_information_restricted_and_resubmit(client, phase4b_context):
    rfq = _create_rfq(client, phase4b_context)
    line = _add_line(client, phase4b_context, rfq)
    assert client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/commands/submit/", {},
        content_type="application/json", **_headers(phase4b_context, "sales")
    ).status_code == 200
    admin_denied = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/review/commands/start/", {},
        content_type="application/json", **_headers(phase4b_context, "admin")
    )
    assert admin_denied.status_code == 403
    assert client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/review/commands/start/", {},
        content_type="application/json", **_headers(phase4b_context, "manager")
    ).status_code == 200
    request_info = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/review/commands/request-information/",
        {"reason": "Clarify notes", "requested_fields": ["notes", "lines"]},
        content_type="application/json", **_headers(phase4b_context, "manager"),
    )
    assert request_info.status_code == 200
    denied_field = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/commands/update/",
        {"project_name": "not requested"}, content_type="application/json",
        **_headers(phase4b_context, "sales"),
    )
    assert denied_field.status_code == 403
    assert client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/commands/update/",
        {"notes": "corrected"}, content_type="application/json",
        **_headers(phase4b_context, "sales"),
    ).status_code == 200
    assert client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/lines/{line.pk}/commands/update/",
        {"technical_notes": "Corrected technical notes"}, content_type="application/json",
        **_headers(phase4b_context, "sales"),
    ).status_code == 200
    assert client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/commands/resubmit/", {},
        content_type="application/json", **_headers(phase4b_context, "sales")
    ).status_code == 200
    rfq.refresh_from_db()
    assert rfq.status == "SUBMITTED"
    assert SalesTechnicalReview.objects.filter(rfq=rfq, decision="NEEDS_INFORMATION").count() == 1


@pytest.mark.django_db
def test_review_complete_and_decline_closure_paths(client, phase4b_context):
    ready = _create_rfq(client, phase4b_context, key="ready-key")
    ready_line = _add_line(client, phase4b_context, ready)
    client.post(f"/api/v1/canonical/rfqs/{ready.pk}/commands/submit/", {}, content_type="application/json", **_headers(phase4b_context, "sales"))
    client.post(f"/api/v1/canonical/rfqs/{ready.pk}/review/commands/start/", {}, content_type="application/json", **_headers(phase4b_context, "manager"))
    complete = client.post(
        f"/api/v1/canonical/rfqs/{ready.pk}/review/commands/complete/",
        {"feasible_line_ids": [ready_line.pk], "drawing_not_required_line_ids": [ready_line.pk], "notes": "Feasible"},
        content_type="application/json", **_headers(phase4b_context, "manager"),
    )
    assert complete.status_code == 200, complete.json()
    ready.refresh_from_db()
    assert ready.status == "READY_TO_QUOTE"

    declined = _create_rfq(client, phase4b_context, key="decline-key")
    _add_line(client, phase4b_context, declined)
    client.post(f"/api/v1/canonical/rfqs/{declined.pk}/commands/submit/", {}, content_type="application/json", **_headers(phase4b_context, "sales"))
    client.post(f"/api/v1/canonical/rfqs/{declined.pk}/review/commands/start/", {}, content_type="application/json", **_headers(phase4b_context, "manager"))
    decline = client.post(
        f"/api/v1/canonical/rfqs/{declined.pk}/review/commands/decline/",
        {"reason": "Not feasible"}, content_type="application/json",
        **_headers(phase4b_context, "manager"),
    )
    assert decline.status_code == 200
    close = client.post(
        f"/api/v1/canonical/rfqs/{declined.pk}/review/commands/acknowledge-declined/",
        {"reason": "Decline acknowledged"}, content_type="application/json",
        **_headers(phase4b_context, "admin"),
    )
    assert close.status_code == 200, close.json()
    declined.refresh_from_db()
    assert declined.status == "CLOSED"


@pytest.mark.django_db
def test_invalid_review_transitions_and_missing_reasons_are_atomic(client, phase4b_context):
    rfq = _create_rfq(client, phase4b_context)
    counts = (SalesTechnicalReview.objects.count(), AuditEvent.objects.count())
    jump = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/review/commands/complete/",
        {"feasible_line_ids": [1]}, content_type="application/json",
        **_headers(phase4b_context, "manager"),
    )
    assert jump.status_code == 409
    blank = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/review/commands/decline/",
        {"reason": ""}, content_type="application/json",
        **_headers(phase4b_context, "manager"),
    )
    assert blank.status_code == 400
    rfq.refresh_from_db()
    assert rfq.status == "DRAFT"
    assert counts == (SalesTechnicalReview.objects.count(), AuditEvent.objects.count())


@pytest.mark.django_db
def test_draft_archive_and_legacy_record_command_denial(client, phase4b_context):
    rfq = _create_rfq(client, phase4b_context)
    archive = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/commands/archive/",
        {"reason": "Request withdrawn"}, content_type="application/json",
        **_headers(phase4b_context, "sales"),
    )
    assert archive.status_code == 200
    legacy = BusinessCustomer.objects.create(
        data_contract="LEGACY", company_name="Historic", contact_name="Historic", status="active"
    )
    denied = client.post(
        f"/api/v1/canonical/customers/{legacy.pk}/commands/update/",
        {"notes": "do not promote"}, content_type="application/json",
        **_headers(phase4b_context, "sales"),
    )
    assert denied.status_code == 403
    legacy.refresh_from_db()
    assert legacy.data_contract == "LEGACY"


@pytest.mark.django_db
def test_upload_rejects_mime_size_signature_and_traversal_without_storage(client, phase4b_context, rfq_storage):
    rfq = _create_rfq(client, phase4b_context)
    _add_line(client, phase4b_context, rfq, drawing_required=True)
    cases = [
        SimpleUploadedFile("bad.exe", b"MZ", content_type="application/octet-stream"),
        SimpleUploadedFile("bad.pdf", b"not-pdf", content_type="application/pdf"),
        SimpleUploadedFile("large.pdf", b"%PDF-" + b"x" * 2048, content_type="application/pdf"),
    ]
    for uploaded in cases:
        response = client.post(
            f"/api/v1/canonical/rfqs/{rfq.pk}/documents/commands/upload/",
            {"file": uploaded, "document_revision": "A"},
            **_headers(phase4b_context, "sales"),
        )
        assert response.status_code == 400
    assert SalesRfqDocument.objects.count() == 0
    assert not list(Path(rfq_storage).rglob("*"))

    class UnsafeUpload:
        name = "../escape.pdf"
        content_type = "application/pdf"
        size = 9

        @staticmethod
        def read(_limit):
            return b"%PDF-safe"

        @staticmethod
        def seek(_position):
            return None

    with pytest.raises(ValidationError, match="safe filename"):
        RfqDocumentSecurityService().validate(UnsafeUpload())


@pytest.mark.django_db
def test_document_version_download_authorization_and_redaction(client, phase4b_context, rfq_storage):
    rfq = _create_rfq(client, phase4b_context)
    line = _add_line(client, phase4b_context, rfq, drawing_required=True)
    first = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/documents/commands/upload/",
        {
            "file": SimpleUploadedFile("folder/drawing.pdf", b"%PDF-v1", content_type="application/pdf"),
            "rfq_line_id": line.pk,
            "document_revision": "A",
        },
        **_headers(phase4b_context, "sales"),
    )
    assert first.status_code == 201, first.json()
    first_data = first.json()["data"]
    assert first_data["original_filename"] == "drawing.pdf"
    assert "storage_key" not in first_data and "path" not in first_data
    document = SalesRfqDocument.objects.get(pk=first_data["id"])
    second = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/documents/{document.pk}/commands/version/",
        {
            "file": SimpleUploadedFile("drawing-v2.pdf", b"%PDF-v2", content_type="application/pdf"),
            "document_revision": "B",
        },
        **_headers(phase4b_context, "sales"),
    )
    assert second.status_code == 201
    newer = SalesRfqDocument.objects.get(pk=second.json()["data"]["id"])
    assert newer.version == 2 and newer.replaces_id == document.pk
    assert document.version == 1 and Path(rfq_storage, document.storage_key).exists()
    download = client.get(
        f"/api/v1/canonical/rfqs/{rfq.pk}/documents/{newer.pk}/download/",
        **_headers(phase4b_context, "manager"),
    )
    assert download.status_code == 200
    assert b"".join(download.streaming_content) == b"%PDF-v2"
    assert "attachment" in download["Content-Disposition"]
    wildcard = client.get(
        f"/api/v1/canonical/rfqs/{rfq.pk}/documents/{newer.pk}/download/",
        **_headers(phase4b_context, "wildcard"),
    )
    assert wildcard.status_code == 403


@pytest.mark.django_db
def test_database_failure_cleans_only_new_upload(client, phase4b_context, rfq_storage, monkeypatch):
    rfq = _create_rfq(client, phase4b_context)
    original = Path(rfq_storage, "rfq_documents", str(rfq.pk), "0" * 32 + ".pdf")
    original.parent.mkdir(parents=True)
    original.write_bytes(b"existing")
    real_save = SalesRfqDocument.save

    def fail_save(self, *args, **kwargs):
        raise RuntimeError("forced database failure")

    monkeypatch.setattr(SalesRfqDocument, "save", fail_save)
    response = client.post(
        f"/api/v1/canonical/rfqs/{rfq.pk}/documents/commands/upload/",
        {"file": SimpleUploadedFile("drawing.pdf", b"%PDF-new", content_type="application/pdf")},
        **_headers(phase4b_context, "sales"),
    )
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    monkeypatch.setattr(SalesRfqDocument, "save", real_save)
    assert original.read_bytes() == b"existing"
    files = [path for path in Path(rfq_storage).rglob("*") if path.is_file()]
    assert files == [original]
    assert SalesRfqDocument.objects.count() == 0


@pytest.mark.django_db
def test_forced_audit_failure_rolls_back_customer_and_number(phase4b_context, monkeypatch):
    before_customers = BusinessCustomer.objects.count()
    before_audits = AuditEvent.objects.count()

    def fail_audit(**kwargs):
        raise RuntimeError("forced audit failure")

    monkeypatch.setattr(command_module, "_audit", fail_audit)
    with pytest.raises(RuntimeError, match="forced audit failure"):
        command_module.MasterDataCommandService.create_customer(
            phase4b_context["users"]["sales"],
            {
                "company_name": "Rollback Buyer", "contact_name": "", "email": "rollback@example.com",
                "phone": "", "country": "Vietnam", "status": "ACTIVE", "notes": "",
            },
        )
    assert BusinessCustomer.objects.count() == before_customers
    assert AuditEvent.objects.count() == before_audits


@pytest.mark.django_db
def test_phase4a_reads_non_mutating_and_legacy_routes_unchanged(client, phase4b_context):
    before = (BusinessCustomer.objects.count(), AuditEvent.objects.count())
    read = client.get("/api/v1/canonical/customers/", **_headers(phase4b_context, "sales"))
    assert read.status_code == 200
    assert before == (BusinessCustomer.objects.count(), AuditEvent.objects.count())
    assert resolve("/api/v1/sales/quotes/").url_name == "api-sales-quotes"
    assert resolve("/api/v1/sales/quotations/").url_name == "api-sales-quotations"
    assert resolve("/api/v1/business/customers/").url_name == "api-business-customers"
    assert resolve("/api/v1/catalog/products/").url_name == "api-catalog-products"
    assert client.put(
        "/api/v1/canonical/customers/commands/create/", {},
        content_type="application/json", **_headers(phase4b_context, "sales")
    ).status_code == 405
    assert TransactionOrder.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_postgresql_twenty_concurrent_rfq_creations_have_unique_numbers(phase4b_context):
    if connection.vendor != "postgresql":
        pytest.skip("Authoritative RFQ concurrency validation requires PostgreSQL")
    actor_id = phase4b_context["users"]["sales"].pk
    customer_id = phase4b_context["customer"].pk
    today = timezone.localdate()
    barrier = Barrier(20)

    def run(index):
        close_old_connections()
        try:
            actor = FoundationUser.objects.select_related("role").get(pk=actor_id)
            barrier.wait()
            rfq, created = RfqCommandService.create(
                actor,
                {
                    "customer_id": customer_id,
                    "project_name": f"Race {index}",
                    "notes": "",
                    "quote_due_at": today + timedelta(days=10),
                    "required_delivery_date": today + timedelta(days=30),
                },
                f"phase4b-race-{index}",
            )
            return rfq.rfq_number, created
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(run, range(20)))
    numbers = [item[0] for item in results]
    assert all(item[1] for item in results)
    assert len(numbers) == len(set(numbers)) == 20
