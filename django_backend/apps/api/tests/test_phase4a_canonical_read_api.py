"""Focused Phase 4A canonical read API and authorization-boundary tests."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import resolve
from django.utils import timezone

from apps.business_core.models import BusinessCustomer, BusinessMaterial, BusinessProduct
from apps.foundation.models import (
    FoundationAuthToken,
    FoundationPermission,
    FoundationRole,
    FoundationUser,
)
from apps.foundation.services import FoundationAuthService
from apps.sales.models import (
    SalesQuotation,
    SalesQuotationApprovalDecision,
    SalesQuotationCustomerDecision,
    SalesQuotationLine,
    SalesRfq,
    SalesRfqDocument,
    SalesRfqLine,
    SalesTechnicalReview,
)
from apps.transaction_domain.models import (
    AuditEvent,
    OrderProgressEvent,
    TransactionOrder,
    TransactionOrderItem,
)


ROLE_PERMISSIONS = {
    "Admin": {
        "customer:view",
        "part:view",
        "material:view",
        "rfq:view",
        "quotation:view",
        "order:view",
        "audit:view",
    },
    "Sales": {
        "customer:view",
        "part:view",
        "material:view",
        "rfq:view",
        "quotation:view",
        "order:view",
    },
    "Manager": {
        "customer:view",
        "part:view",
        "material:view",
        "rfq:view",
        "quotation:view",
        "order:view",
        "audit:view",
    },
}


def _permission(code):
    module, action = code.split(":", 1)
    permission, _created = FoundationPermission.objects.get_or_create(
        code=code,
        defaults={"module": module, "action": action, "description": "Phase 4A test"},
    )
    if permission.module != module or permission.action != action:
        permission.module = module
        permission.action = action
        permission.save(update_fields=["module", "action"])
    return permission


def _user(role_name, *, suffix, permissions=(), active=True):
    role, _created = FoundationRole.objects.get_or_create(
        name=role_name,
        defaults={"description": f"Phase 4A {role_name}"},
    )
    for code in permissions:
        role.permissions.add(_permission(code))
    return FoundationUser.objects.create(
        email=f"{suffix}@phase4a.example",
        full_name=f"Phase 4A {suffix}",
        password_hash="not-exposed",
        role=role,
        is_active=active,
    )


def _token(user, suffix):
    raw = f"phase4a-{suffix}-token"
    FoundationAuthToken.objects.create(
        user=user,
        token_hash=FoundationAuthService.hash_token(raw),
        expires_at=timezone.now() + timedelta(hours=1),
        remote_addr="127.0.0.1",
        user_agent="phase4a-test",
    )
    return raw


@pytest.fixture
def phase4a_context(db):
    users = {}
    tokens = {}
    for role_name, permissions in ROLE_PERMISSIONS.items():
        key = role_name.lower()
        users[key] = _user(role_name, suffix=key, permissions=permissions)
        tokens[key] = _token(users[key], key)

    users["inactive"] = _user(
        "Sales", suffix="inactive", permissions=ROLE_PERMISSIONS["Sales"], active=False
    )
    tokens["inactive"] = _token(users["inactive"], "inactive")
    users["unassigned"] = _user("Unassigned", suffix="unassigned")
    tokens["unassigned"] = _token(users["unassigned"], "unassigned")
    users["malformed"] = _user(
        "sales", suffix="malformed", permissions={"customer:view"}
    )
    tokens["malformed"] = _token(users["malformed"], "malformed")
    users["wildcard"] = _user("Wildcard", suffix="wildcard")
    wildcard_permission, _created = FoundationPermission.objects.get_or_create(
        code="*:*",
        defaults={"module": "*", "action": "*", "description": "Legacy wildcard"},
    )
    users["wildcard"].role.permissions.add(wildcard_permission)
    tokens["wildcard"] = _token(users["wildcard"], "wildcard")

    customer = BusinessCustomer.objects.create(
        data_contract="MVP_V1",
        customer_code="CUS-4A-001",
        company_name="Canonical Customer",
        contact_name="Business Contact",
        email="contact@example.com",
        phone="+81000000001",
        country="Japan",
        status="ACTIVE",
        created_by=users["sales"],
    )
    legacy_customer = BusinessCustomer.objects.create(
        data_contract="LEGACY",
        legacy_customer_id=40401,
        company_name="Legacy Customer",
        contact_name="Legacy Contact",
        status="active",
    )
    material = BusinessMaterial.objects.create(
        data_contract="MVP_V1",
        material_code="MAT-4A-001",
        name="SUS304",
        standard="JIS",
        grade="304",
        created_by=users["admin"],
    )
    part = BusinessProduct.objects.create(
        data_contract="MVP_V1",
        part_code="PART-4A-001",
        revision="A",
        unit="PCS",
        default_material=material,
        name="Canonical Part",
        slug="canonical-part-4a-001",
        price=Decimal("99.9900"),
        created_by=users["admin"],
    )
    today = date.today()
    rfq = SalesRfq.objects.create(
        data_contract="MVP_V1",
        rfq_number="RFQ-2026-4A01",
        quotation_family_number="QT-2026-4A01",
        customer=customer,
        status="READY_TO_QUOTE",
        project_name="Phase 4A fixture",
        quote_due_at=today + timedelta(days=7),
        required_delivery_date=today + timedelta(days=30),
        assigned_to=users["sales"],
        created_by=users["sales"],
    )
    rfq_line = SalesRfqLine.objects.create(
        rfq=rfq,
        line_number=1,
        part=part,
        material=material,
        description="Precision shaft",
        quantity=Decimal("2.5000"),
        unit="PCS",
        required_delivery_date=today + timedelta(days=30),
        tolerance="0.01 mm",
        technical_notes="Inspect finish",
        drawing_required=True,
    )
    document = SalesRfqDocument.objects.create(
        rfq=rfq,
        rfq_line=rfq_line,
        original_filename="shaft.step",
        storage_key="private/internal/secret-path/shaft.step",
        mime_type="application/step",
        size_bytes=1024,
        checksum_sha256="a" * 64,
        document_revision="A",
        uploaded_by=users["sales"],
    )
    review = SalesTechnicalReview.objects.create(
        rfq=rfq,
        reviewer=users["manager"],
        decision="READY_TO_QUOTE",
        notes="Technically feasible",
    )
    quotation = SalesQuotation.objects.create(
        customer=customer,
        data_contract="MVP_V1",
        rfq=rfq,
        quotation_number="QT-2026-4A01-R0",
        version=1,
        revision=0,
        status="draft",
        workflow_status="DRAFT",
        approval_status="pending",
        currency="USD",
        valid_from=today,
        valid_until=today + timedelta(days=14),
        subtotal=Decimal("250.0000"),
        discount_total=Decimal("10.0000"),
        tax_amount=Decimal("24.0000"),
        total=Decimal("264.0000"),
        terms="Net 30",
        customer_snapshot={
            "id": customer.pk,
            "customer_code": customer.customer_code,
            "company_name": customer.company_name,
            "contact_name": customer.contact_name,
            "email": "snapshot-private@example.com",
            "phone": "+81999999999",
        },
        rfq_snapshot={"id": rfq.pk, "rfq_number": rfq.rfq_number},
        idempotency_key="phase4a-quote-key",
        request_hash="b" * 64,
        created_by=users["sales"],
    )
    quote_line = SalesQuotationLine.objects.create(
        quotation=quotation,
        data_contract="MVP_V1",
        line_number=1,
        source_rfq_line=rfq_line,
        product=part,
        description="Precision shaft",
        part_code_snapshot=part.part_code,
        material_snapshot="MAT-4A-001 - SUS304",
        unit="PCS",
        quantity=Decimal("2.5000"),
        unit_price=Decimal("100.0000"),
        discount=Decimal("10.0000"),
        line_subtotal=Decimal("250.0000"),
        line_total=Decimal("240.0000"),
    )
    SalesQuotation.objects.filter(pk=quotation.pk).update(
        workflow_status="SENT",
        status="sent",
        approval_status="approved",
        sent_at=timezone.now(),
    )
    quotation.refresh_from_db()
    approval = SalesQuotationApprovalDecision.objects.create(
        quotation=quotation,
        reviewer=users["manager"],
        decision="APPROVED",
        notes="Commercial approval",
    )
    customer_decision = SalesQuotationCustomerDecision.objects.create(
        quotation=quotation,
        recorded_by=users["sales"],
        decision="ACCEPTED",
        contact_snapshot="private-contact@example.com",
        evidence="Customer email confirmation",
    )
    order = TransactionOrder(
        order_number="SO-2026-4A01",
        customer=customer,
        data_contract="MVP_V1",
        source_quotation=quotation,
        source_rfq=rfq,
        workflow_status="CONFIRMED",
        currency="USD",
        subtotal=Decimal("250.0000"),
        discount_total=Decimal("10.0000"),
        tax_amount=Decimal("24.0000"),
        total_amount=Decimal("264.0000"),
        customer_snapshot={"customer_code": customer.customer_code},
        quotation_snapshot={"quotation_number": quotation.quotation_number},
        ordered_at=timezone.now(),
        expected_delivery_date=today + timedelta(days=30),
        progress_percent=0,
        source_quotation_sent_at=quotation.sent_at,
        idempotency_key="phase4a-order-key",
        request_hash="c" * 64,
        created_by=users["sales"],
    )
    order._phase3d_conversion_authorized = True
    order.save()
    order_line = TransactionOrderItem(
        order=order,
        product=part,
        data_contract="MVP_V1",
        line_number=1,
        source_quotation_line=quote_line,
        description_snapshot="Precision shaft",
        part_code_snapshot=part.part_code,
        material_snapshot="MAT-4A-001 - SUS304",
        quantity=Decimal("2.5000"),
        unit="PCS",
        unit_price=Decimal("100.0000"),
        line_total=Decimal("240.0000"),
    )
    order_line._phase3d_conversion_authorized = True
    order_line.save()
    progress = OrderProgressEvent.objects.create(
        order=order,
        from_status="",
        to_status="CONFIRMED",
        progress_percent=0,
        milestone_note="Order confirmed",
        actor=users["sales"],
    )
    audit = AuditEvent.objects.create(
        actor_ref=f"user:{users['sales'].pk}",
        actor_display=users["sales"].full_name,
        actor_user=users["sales"],
        action="order.converted",
        entity_type="order",
        entity_id=str(order.pk),
        new_status="CONFIRMED",
        metadata={
            "source_quotation_id": quotation.pk,
            "source_quotation_number": quotation.quotation_number,
            "line_count": 1,
        },
    )
    return {
        "users": users,
        "tokens": tokens,
        "customer": customer,
        "legacy_customer": legacy_customer,
        "material": material,
        "part": part,
        "rfq": rfq,
        "rfq_line": rfq_line,
        "document": document,
        "review": review,
        "quotation": quotation,
        "quote_line": quote_line,
        "approval": approval,
        "customer_decision": customer_decision,
        "order": order,
        "order_line": order_line,
        "progress": progress,
        "audit": audit,
    }


def _auth(context, role):
    return {"HTTP_AUTHORIZATION": f"Bearer {context['tokens'][role]}"}


@pytest.mark.django_db
def test_unauthenticated_inactive_unassigned_malformed_and_wildcard_fail_closed(
    client, phase4a_context
):
    url = "/api/v1/canonical/customers/"
    unauthenticated = client.get(url)
    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["error"]["code"] == "authentication_required"

    expected = {
        "inactive": (401, "authentication_failed"),
        "unassigned": (403, "permission_denied"),
        "malformed": (403, "permission_denied"),
        "wildcard": (403, "permission_denied"),
    }
    for role, (status_code, code) in expected.items():
        response = client.get(url, **_auth(phase4a_context, role))
        assert response.status_code == status_code
        assert response.json()["error"]["code"] == code


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["admin", "sales", "manager"])
def test_admin_sales_manager_read_matrix_and_all_internal_visibility(
    client, phase4a_context, role
):
    for url in (
        "/api/v1/canonical/customers/",
        "/api/v1/canonical/parts/",
        "/api/v1/canonical/materials/",
        "/api/v1/canonical/rfqs/",
        "/api/v1/canonical/quotation-families/",
        "/api/v1/canonical/quotations/",
        "/api/v1/canonical/orders/",
    ):
        response = client.get(url, **_auth(phase4a_context, role))
        assert response.status_code == 200, (url, response.content)
        assert response.json()["data"]["count"] >= 1


@pytest.mark.django_db
def test_all_canonical_detail_and_nested_resources_are_readable(client, phase4a_context):
    context = phase4a_context
    headers = _auth(context, "admin")
    urls = (
        f"/api/v1/canonical/customers/{context['customer'].pk}/",
        f"/api/v1/canonical/parts/{context['part'].pk}/",
        f"/api/v1/canonical/materials/{context['material'].pk}/",
        f"/api/v1/canonical/rfqs/{context['rfq'].pk}/",
        f"/api/v1/canonical/rfqs/{context['rfq'].pk}/lines/",
        f"/api/v1/canonical/rfqs/{context['rfq'].pk}/documents/",
        f"/api/v1/canonical/rfqs/{context['rfq'].pk}/technical-reviews/",
        "/api/v1/canonical/quotation-families/QT-2026-4A01/",
        "/api/v1/canonical/quotation-families/QT-2026-4A01/revisions/",
        f"/api/v1/canonical/quotations/{context['quotation'].pk}/",
        f"/api/v1/canonical/quotations/{context['quotation'].pk}/lines/",
        f"/api/v1/canonical/quotations/{context['quotation'].pk}/approval-decisions/",
        f"/api/v1/canonical/quotations/{context['quotation'].pk}/customer-decisions/",
        f"/api/v1/canonical/orders/{context['order'].pk}/",
        f"/api/v1/canonical/orders/{context['order'].pk}/lines/",
        f"/api/v1/canonical/orders/{context['order'].pk}/progress/",
        f"/api/v1/canonical/timelines/order/{context['order'].pk}/",
        "/api/v1/canonical/audit-events/",
    )
    for url in urls:
        response = client.get(url, **headers)
        assert response.status_code == 200, (url, response.content)
        assert response.json()["success"] is True


@pytest.mark.django_db
def test_uppercase_status_timezone_and_exact_decimal_serialization(client, phase4a_context):
    context = phase4a_context
    headers = _auth(context, "sales")
    quote = client.get(
        f"/api/v1/canonical/quotations/{context['quotation'].pk}/", **headers
    ).json()["data"]
    order = client.get(
        f"/api/v1/canonical/orders/{context['order'].pk}/", **headers
    ).json()["data"]
    line = client.get(
        f"/api/v1/canonical/quotations/{context['quotation'].pk}/lines/", **headers
    ).json()["data"]["results"][0]

    assert quote["workflow_status"] == "SENT"
    assert order["workflow_status"] == "CONFIRMED"
    assert quote["total"] == "264.0000"
    assert order["total_amount"] == "264.0000"
    assert line["quantity"] == "2.5000"
    assert timezone.datetime.fromisoformat(order["ordered_at"]).tzinfo is not None


@pytest.mark.django_db
def test_pagination_allowed_filters_ordering_and_unsupported_query_rejection(
    client, phase4a_context
):
    headers = _auth(phase4a_context, "admin")
    response = client.get(
        "/api/v1/canonical/customers/?data_contract=MVP_V1&ordering=-customer_code&limit=1&offset=0",
        **headers,
    )
    assert response.status_code == 200
    page = response.json()["data"]
    assert page["limit"] == 1
    assert page["count"] == 1
    assert page["results"][0]["customer_code"] == "CUS-4A-001"

    too_large = client.get("/api/v1/canonical/customers/?limit=101", **headers)
    unsupported = client.get("/api/v1/canonical/customers/?password_hash=x", **headers)
    bad_order = client.get("/api/v1/canonical/customers/?ordering=notes", **headers)
    assert too_large.status_code == 400
    assert too_large.json()["error"]["code"] == "invalid_query_parameter"
    assert unsupported.json()["error"]["code"] == "unsupported_filter"
    assert bad_order.json()["error"]["code"] == "unsupported_ordering"


@pytest.mark.django_db
def test_security_redaction_and_no_internal_document_path(client, phase4a_context):
    context = phase4a_context
    headers = _auth(context, "admin")
    urls = (
        f"/api/v1/canonical/rfqs/{context['rfq'].pk}/documents/",
        f"/api/v1/canonical/quotations/{context['quotation'].pk}/",
        f"/api/v1/canonical/quotations/{context['quotation'].pk}/customer-decisions/",
        "/api/v1/canonical/audit-events/",
    )
    payload = " ".join(str(client.get(url, **headers).json()).lower() for url in urls)
    for forbidden in (
        "password_hash",
        "token_hash",
        "idempotency_key",
        "request_hash",
        "storage_key",
        "private/internal/secret-path",
        "snapshot-private@example.com",
        "private-contact@example.com",
    ):
        assert forbidden not in payload


@pytest.mark.django_db
def test_reads_do_not_mutate_domain_or_create_audit_events(client, phase4a_context):
    context = phase4a_context
    headers = _auth(context, "manager")
    before = {
        "orders": TransactionOrder.objects.count(),
        "progress": OrderProgressEvent.objects.count(),
        "audit": AuditEvent.objects.count(),
        "quote_status": SalesQuotation.objects.get(pk=context["quotation"].pk).workflow_status,
        "order_status": TransactionOrder.objects.get(pk=context["order"].pk).workflow_status,
    }
    client.get("/api/v1/canonical/rfqs/", **headers)
    client.get(f"/api/v1/canonical/quotations/{context['quotation'].pk}/", **headers)
    client.get(f"/api/v1/canonical/orders/{context['order'].pk}/progress/", **headers)
    client.get(f"/api/v1/canonical/timelines/order/{context['order'].pk}/", **headers)
    after = {
        "orders": TransactionOrder.objects.count(),
        "progress": OrderProgressEvent.objects.count(),
        "audit": AuditEvent.objects.count(),
        "quote_status": SalesQuotation.objects.get(pk=context["quotation"].pk).workflow_status,
        "order_status": TransactionOrder.objects.get(pk=context["order"].pk).workflow_status,
    }
    assert after == before


@pytest.mark.django_db
def test_sales_entity_timeline_allowed_but_global_audit_denied(client, phase4a_context):
    context = phase4a_context
    headers = _auth(context, "sales")
    timeline = client.get(
        f"/api/v1/canonical/timelines/order/{context['order'].pk}/", **headers
    )
    global_audit = client.get("/api/v1/canonical/audit-events/", **headers)
    assert timeline.status_code == 200
    assert timeline.json()["data"]["count"] == 1
    assert global_audit.status_code == 403
    assert global_audit.json()["error"]["code"] == "permission_denied"


@pytest.mark.django_db
def test_legacy_record_has_explicit_compatibility_and_is_not_promoted(client, phase4a_context):
    context = phase4a_context
    response = client.get(
        f"/api/v1/canonical/customers/{context['legacy_customer'].pk}/",
        **_auth(context, "sales"),
    )
    data = response.json()["data"]
    context["legacy_customer"].refresh_from_db()
    assert data["data_contract"] == "LEGACY"
    assert data["status"] is None
    assert data["compatibility"] == {
        "representation": "LEGACY",
        "legacy_customer_id": 40401,
        "legacy_status": "active",
    }
    assert context["legacy_customer"].data_contract == "LEGACY"


@pytest.mark.django_db
def test_unsafe_methods_have_consistent_denial_envelope(client, phase4a_context):
    headers = _auth(phase4a_context, "admin")
    for method in ("post", "put", "patch", "delete"):
        response = getattr(client, method)(
            "/api/v1/canonical/customers/",
            data={},
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 405
        assert response.json() == {
            "success": False,
            "error": {
                "code": "method_not_allowed",
                "message": "Only GET, HEAD, and OPTIONS are allowed.",
            },
        }


@pytest.mark.django_db
def test_head_and_options_are_authenticated_safe_methods(client, phase4a_context):
    url = "/api/v1/canonical/customers/"
    assert client.options(url).status_code == 401
    headers = _auth(phase4a_context, "admin")
    assert client.head(url, **headers).status_code == 200
    assert client.options(url, **headers).status_code == 200


@pytest.mark.django_db
def test_representative_list_query_count_does_not_scale_with_rows(client, phase4a_context):
    context = phase4a_context
    headers = _auth(context, "admin")
    with CaptureQueriesContext(connection) as first_capture:
        response = client.get("/api/v1/canonical/customers/?limit=20", **headers)
    assert response.status_code == 200

    for index in range(5):
        BusinessCustomer.objects.create(
            data_contract="MVP_V1",
            customer_code=f"CUS-4A-{index + 100}",
            company_name=f"Customer {index}",
            contact_name="Contact",
            email=f"customer{index}@example.com",
            status="ACTIVE",
            created_by=context["users"]["sales"],
        )
    with CaptureQueriesContext(connection) as larger_capture:
        response = client.get("/api/v1/canonical/customers/?limit=20", **headers)
    assert response.status_code == 200
    assert len(larger_capture) == len(first_capture)
    assert len(larger_capture) <= 4


def test_rfq_quotation_terminology_and_legacy_route_contracts_are_unchanged():
    quote_route = resolve("/api/v1/sales/quotes/")
    quotation_route = resolve("/api/v1/sales/quotations/")
    canonical_rfq = resolve("/api/v1/canonical/rfqs/")
    canonical_family = resolve("/api/v1/canonical/quotation-families/")
    canonical_quotation = resolve("/api/v1/canonical/quotations/")

    assert quote_route.url_name == "api-sales-quotes"
    assert set(quote_route.func.cls.http_method_names) >= {"get", "post"}
    assert quotation_route.url_name == "api-sales-quotations"
    assert set(quotation_route.func.cls.http_method_names) >= {"get", "post"}
    assert canonical_rfq.url_name == "canonical-rfq-list"
    assert canonical_family.url_name == "canonical-quotation-family-list"
    assert canonical_quotation.url_name == "canonical-quotation-list"
    assert "post" not in canonical_rfq.func.view_class.http_method_names


@pytest.mark.django_db
def test_error_envelope_codes_for_not_found_and_unsupported_entity(client, phase4a_context):
    headers = _auth(phase4a_context, "admin")
    missing = client.get("/api/v1/canonical/customers/999999/", **headers)
    unsupported = client.get("/api/v1/canonical/timelines/user/1/", **headers)
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"
    assert unsupported.status_code == 400
    assert unsupported.json()["error"]["code"] == "unsupported_entity_type"
