"""Migration-path, legacy preservation, reverse, and RBAC tests for Phase 3D."""

from decimal import Decimal

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


BEFORE_PHASE3D = [
    ("foundation", "0008_define_phase3c_permissions"),
    ("sales", "0005_phase3c_quotation_constraints"),
    ("transaction_domain", "0002_seed_transaction_domain_from_legacy"),
]
AFTER_PHASE3D = [
    ("transaction_domain", "0005_phase3d_order_constraints"),
]

EXPECTED_ROLE_GRANTS = {
    "Admin": {
        "user:view", "user:manage",
        "customer:view", "customer:create", "customer:change", "customer:archive",
        "part:view", "part:manage", "part:archive",
        "material:view", "material:manage", "material:archive",
        "rfq:view", "rfq:create", "rfq:change", "rfq:archive", "rfq:submit",
        "rfq:document_upload", "rfq:document_download",
        "quotation:view", "quotation:create_revision", "quotation:change",
        "quotation:submit", "quotation:send", "quotation:record_customer_decision",
        "quotation:convert", "order:view", "order:progress", "order:hold",
        "order:resume", "order:complete", "order:cancel", "audit:view",
    },
    "Sales": {
        "customer:view", "customer:create", "customer:change", "customer:archive",
        "part:view", "material:view", "rfq:view", "rfq:create", "rfq:change",
        "rfq:archive", "rfq:submit", "rfq:document_upload", "rfq:document_download",
        "quotation:view", "quotation:create_revision", "quotation:change",
        "quotation:submit", "quotation:send", "quotation:record_customer_decision",
        "quotation:convert", "order:view",
    },
    "Manager": {
        "customer:view", "part:view", "material:view", "rfq:view", "rfq:review",
        "rfq:document_download", "quotation:view", "quotation:approve",
        "quotation:reject", "order:view", "order:progress", "order:hold",
        "order:resume", "order:complete", "order:cancel", "audit:view",
    },
}


def migrate_to(targets):
    executor = MigrationExecutor(connection)
    executor.migrate(targets)
    return MigrationExecutor(connection)


@pytest.mark.django_db(transaction=True)
def test_phase3d_clean_migration_schema_rbac_and_safe_reverse():
    migrate_to(BEFORE_PHASE3D)
    executor = migrate_to(AFTER_PHASE3D)
    apps = executor.loader.project_state(AFTER_PHASE3D).apps
    tables = set(connection.introspection.table_names())

    assert "transaction_order_progress_events" in tables
    assert "transaction_audit_events" in tables
    order_model = apps.get_model("transaction_domain", "TransactionOrder")
    line_model = apps.get_model("transaction_domain", "TransactionOrderItem")
    assert {
        "data_contract", "source_quotation", "source_rfq", "workflow_status",
        "currency", "subtotal", "discount_total", "tax_amount", "customer_snapshot",
        "quotation_snapshot", "ordered_at", "expected_delivery_date", "progress_percent",
        "hold_reason", "cancel_reason", "source_quotation_sent_at", "completed_at_v1",
        "idempotency_key", "request_hash", "created_by", "updated_by",
    } <= {field.name for field in order_model._meta.fields}
    assert {
        "data_contract", "line_number", "source_quotation_line", "description_snapshot",
        "part_code_snapshot", "material_snapshot", "unit",
    } <= {field.name for field in line_model._meta.fields}

    role_model = apps.get_model("foundation", "FoundationRole")
    for role_name, expected in EXPECTED_ROLE_GRANTS.items():
        role = role_model.objects.get(name=role_name)
        actual = set(role.permissions.values_list("code", flat=True))
        assert actual == expected
        assert role.users.count() == 0

    migrate_to(BEFORE_PHASE3D)
    tables = set(connection.introspection.table_names())
    assert "transaction_order_progress_events" not in tables
    assert "transaction_audit_events" not in tables
    migrate_to(AFTER_PHASE3D)


@pytest.mark.django_db(transaction=True)
def test_mig_201_legacy_order_item_history_and_approval_are_preserved():
    executor = migrate_to(BEFORE_PHASE3D)
    old_apps = executor.loader.project_state(BEFORE_PHASE3D).apps
    role_model = old_apps.get_model("foundation", "FoundationRole")
    user_model = old_apps.get_model("foundation", "FoundationUser")
    customer_model = old_apps.get_model("business_core", "BusinessCustomer")
    order_model = old_apps.get_model("transaction_domain", "TransactionOrder")
    line_model = old_apps.get_model("transaction_domain", "TransactionOrderItem")
    status_model = old_apps.get_model("transaction_domain", "OrderStatusHistory")
    history_model = old_apps.get_model("transaction_domain", "TransactionHistory")
    approval_model = old_apps.get_model("transaction_domain", "WorkflowApproval")

    role = role_model.objects.create(name="legacy-phase3d-role")
    user = user_model.objects.create(
        email="legacy-preflight@example.com",
        full_name="Legacy Assignee",
        password_hash="historic-hash",
        role=role,
    )
    customer = customer_model.objects.create(
        legacy_customer_id=3201,
        company_name="Historic Customer",
        contact_name="Historic Contact",
        email="historic@example.com",
        phone="0123456789",
        status="active",
    )
    order = order_model.objects.create(
        legacy_quote_request_id=3202,
        order_number="ORD-LQ-003202",
        customer=customer,
        project_name="Historic project",
        message="Historic message",
        status="processing",
        assigned_to=user,
        internal_note="Historic note",
        total_amount=Decimal("1234.56"),
        quoted_at="2024-01-02 legacy text",
        completed_at="",
    )
    line = line_model.objects.create(
        legacy_quote_item_id=3203,
        order=order,
        drawing_code="DRAW-OLD",
        material_name="S45C",
        quantity=7,
        tolerance="H7",
        note="Historic line note",
        unit_price=Decimal("12.34"),
        line_total=Decimal("86.38"),
    )
    status = status_model.objects.create(
        order=order,
        from_status="approved",
        to_status="processing",
        actor="historic-manager",
        note="Historic status note",
    )
    history = history_model.objects.create(
        legacy_event_id=3204,
        order=order,
        entity_type="workflow",
        entity_id=str(order.pk),
        action="workflow.transition",
        actor="historic-manager",
        payload={"original": True, "value": "unchanged"},
    )
    approval = approval_model.objects.create(
        order=order,
        requested_status="processing",
        decision="approved",
        requested_by="historic-requester",
        reviewed_by="historic-reviewer",
        note="Historic approval note",
    )
    expected = {
        "order": list(order_model.objects.filter(pk=order.pk).values())[0],
        "line": list(line_model.objects.filter(pk=line.pk).values())[0],
        "status": list(status_model.objects.filter(pk=status.pk).values())[0],
        "history": list(history_model.objects.filter(pk=history.pk).values())[0],
        "approval": list(approval_model.objects.filter(pk=approval.pk).values())[0],
    }

    executor = migrate_to(AFTER_PHASE3D)
    apps = executor.loader.project_state(AFTER_PHASE3D).apps
    new_order_model = apps.get_model("transaction_domain", "TransactionOrder")
    new_line_model = apps.get_model("transaction_domain", "TransactionOrderItem")
    new_status_model = apps.get_model("transaction_domain", "OrderStatusHistory")
    new_history_model = apps.get_model("transaction_domain", "TransactionHistory")
    new_approval_model = apps.get_model("transaction_domain", "WorkflowApproval")
    migrated_order = new_order_model.objects.get(pk=order.pk)
    migrated_line = new_line_model.objects.get(pk=line.pk)

    for field, value in expected["order"].items():
        assert getattr(migrated_order, field) == value
    for field, value in expected["line"].items():
        assert getattr(migrated_line, field) == value
    assert new_status_model.objects.filter(**expected["status"]).count() == 1
    assert new_history_model.objects.filter(**expected["history"]).count() == 1
    assert new_approval_model.objects.filter(**expected["approval"]).count() == 1
    assert migrated_order.data_contract == "LEGACY"
    assert migrated_order.source_quotation_id is None
    assert migrated_order.source_rfq_id is None
    assert migrated_order.workflow_status is None
    assert migrated_order.idempotency_key is None
    assert migrated_line.data_contract == "LEGACY"
    assert migrated_line.line_number is None
    assert migrated_line.source_quotation_line_id is None
    assert apps.get_model("transaction_domain", "OrderProgressEvent").objects.count() == 0
    assert apps.get_model("transaction_domain", "AuditEvent").objects.count() == 0


def test_phase3d_migrations_do_not_read_external_legacy_sources():
    migration_root = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "apps" / "transaction_domain" / "migrations"
    )
    for migration_name in (
        "0003_phase3d_order_schema.py",
        "0004_classify_phase3d_legacy_orders.py",
        "0005_phase3d_order_constraints.py",
    ):
        source = (migration_root / migration_name).read_text(encoding="utf-8")
        assert "sqlite3" not in source
        assert "legacy_database" not in source
        assert "DATABASE_URL" not in source
