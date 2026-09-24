"""Migration-path verification for the Phase 3C quotation boundaries."""

from decimal import Decimal
from pathlib import Path

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


BEFORE_PHASE3C = [
    ("foundation", "0007_define_phase3b_permissions"),
    ("sales", "0002_salesrfq_salesrfqline_salesrfqdocument_and_more"),
]
AFTER_PHASE3C = [
    ("foundation", "0008_define_phase3c_permissions"),
    ("sales", "0005_phase3c_quotation_constraints"),
]
PHASE3C_PERMISSION_CODES = {
    "quotation:view",
    "quotation:create_revision",
    "quotation:change",
    "quotation:submit",
    "quotation:approve",
    "quotation:reject",
    "quotation:send",
    "quotation:record_customer_decision",
    "quotation:convert",
}


def migrate_to(targets):
    executor = MigrationExecutor(connection)
    executor.migrate(targets)
    return MigrationExecutor(connection)


@pytest.mark.django_db(transaction=True)
def test_phase3c_clean_migration_creates_schema_and_permissions_without_grants():
    try:
        migrate_to(BEFORE_PHASE3C)
        executor = migrate_to(AFTER_PHASE3C)
        apps = executor.loader.project_state(AFTER_PHASE3C).apps
        table_names = set(connection.introspection.table_names())

        assert "sales_quotation_approval_decisions" in table_names
        assert "sales_quotation_customer_decisions" in table_names
        quotation_model = apps.get_model("sales", "SalesQuotation")
        line_model = apps.get_model("sales", "SalesQuotationLine")
        assert {
            "data_contract",
            "rfq",
            "revision",
            "workflow_status",
            "currency",
            "valid_from",
            "valid_until",
            "tax_amount",
            "customer_snapshot",
            "rfq_snapshot",
            "idempotency_key",
        }.issubset({field.name for field in quotation_model._meta.fields})
        assert {
            "data_contract",
            "line_number",
            "source_rfq_line",
            "part_code_snapshot",
            "material_snapshot",
            "unit",
            "line_subtotal",
        }.issubset({field.name for field in line_model._meta.fields})

        permission_model = apps.get_model("foundation", "FoundationPermission")
        relation_model = apps.get_model("foundation", "FoundationRolePermission")
        permissions = permission_model.objects.filter(code__in=PHASE3C_PERMISSION_CODES)
        assert set(permissions.values_list("code", flat=True)) == PHASE3C_PERMISSION_CODES
        assert relation_model.objects.filter(permission__in=permissions).count() == 0
    finally:
        migrate_to(AFTER_PHASE3C)


@pytest.mark.django_db(transaction=True)
def test_phase3c_existing_quotation_rows_remain_legacy_exact_and_unlinked():
    try:
        old_executor = migrate_to(BEFORE_PHASE3C)
        old_apps = old_executor.loader.project_state(BEFORE_PHASE3C).apps
        quotation_model = old_apps.get_model("sales", "SalesQuotation")
        line_model = old_apps.get_model("sales", "SalesQuotationLine")
        quotation = quotation_model.objects.create(
            quotation_number="SQ-HISTORIC-0001",
            version=9,
            status="accepted",
            approval_status="approved",
            subtotal=Decimal("123.45"),
            discount_total=Decimal("3.45"),
            total=Decimal("120.00"),
        )
        line = line_model.objects.create(
            quotation=quotation,
            description="Historic precision line",
            quantity=Decimal("2.50"),
            unit_price=Decimal("50.00"),
            discount=Decimal("0.00"),
            line_total=Decimal("125.00"),
        )
        original_quote_id = quotation.pk
        original_line_id = line.pk

        new_executor = migrate_to(AFTER_PHASE3C)
        new_apps = new_executor.loader.project_state(AFTER_PHASE3C).apps
        new_quotation_model = new_apps.get_model("sales", "SalesQuotation")
        new_line_model = new_apps.get_model("sales", "SalesQuotationLine")
        approval_model = new_apps.get_model("sales", "SalesQuotationApprovalDecision")
        customer_decision_model = new_apps.get_model("sales", "SalesQuotationCustomerDecision")
        migrated = new_quotation_model.objects.get(pk=original_quote_id)
        migrated_line = new_line_model.objects.get(pk=original_line_id)

        assert migrated.quotation_number == "SQ-HISTORIC-0001"
        assert migrated.version == 9
        assert migrated.status == "accepted"
        assert migrated.approval_status == "approved"
        assert migrated.subtotal == Decimal("123.4500")
        assert migrated.discount_total == Decimal("3.4500")
        assert migrated.total == Decimal("120.0000")
        assert migrated.data_contract == "LEGACY"
        assert migrated.rfq_id is None
        assert migrated.revision is None
        assert migrated.workflow_status is None
        assert migrated.currency is None
        assert migrated.idempotency_key is None
        assert migrated.request_hash == ""
        assert migrated.customer_snapshot == {}
        assert migrated.rfq_snapshot == {}
        assert migrated_line.description == "Historic precision line"
        assert migrated_line.quantity == Decimal("2.5000")
        assert migrated_line.unit_price == Decimal("50.0000")
        assert migrated_line.line_total == Decimal("125.0000")
        assert migrated_line.data_contract == "LEGACY"
        assert migrated_line.line_number is None
        assert migrated_line.source_rfq_line_id is None
        assert approval_model.objects.count() == 0
        assert customer_decision_model.objects.count() == 0

        reversed_executor = migrate_to(BEFORE_PHASE3C)
        reversed_apps = reversed_executor.loader.project_state(BEFORE_PHASE3C).apps
        reversed_quotation = reversed_apps.get_model("sales", "SalesQuotation").objects.get(
            pk=original_quote_id
        )
        reversed_line = reversed_apps.get_model("sales", "SalesQuotationLine").objects.get(
            pk=original_line_id
        )
        assert reversed_quotation.quotation_number == "SQ-HISTORIC-0001"
        assert reversed_quotation.version == 9
        assert reversed_quotation.status == "accepted"
        assert reversed_quotation.approval_status == "approved"
        assert reversed_quotation.subtotal == Decimal("123.45")
        assert reversed_line.description == "Historic precision line"
        assert reversed_line.quantity == Decimal("2.50")
    finally:
        migrate_to(AFTER_PHASE3C)


def test_phase3c_migrations_do_not_access_external_legacy_database():
    backend_root = Path(__file__).resolve().parents[1]
    migration_paths = [
        backend_root / "apps/foundation/migrations/0008_define_phase3c_permissions.py",
        backend_root / "apps/sales/migrations/0003_phase3c_quotation_schema.py",
        backend_root / "apps/sales/migrations/0004_classify_phase3c_legacy_quotations.py",
        backend_root / "apps/sales/migrations/0005_phase3c_quotation_constraints.py",
    ]
    forbidden_tokens = (
        "LEGACY_DATABASE",
        '.using("legacy")',
        ".using('legacy')",
        "QuoteRequest",
        "quote_requests",
    )
    for path in migration_paths:
        migration_source = path.read_text(encoding="utf-8")
        assert all(token not in migration_source for token in forbidden_tokens)
