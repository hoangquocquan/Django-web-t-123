"""Migration-path verification for the additive Phase 3B schema."""

from pathlib import Path

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


BEFORE_PHASE3B = [
    ("foundation", "0006_add_login_audit_and_two_factor_challenges"),
    ("business_core", "0002_seed_business_core_from_legacy"),
    ("sales", "0001_sales_platform"),
]
AFTER_PHASE3B = [
    ("foundation", "0007_define_phase3b_permissions"),
    ("business_core", "0005_phase3b_master_constraints"),
    ("sales", "0002_salesrfq_salesrfqline_salesrfqdocument_and_more"),
]
PHASE3B_PERMISSION_CODES = {
    "customer:view",
    "customer:create",
    "customer:change",
    "customer:archive",
    "part:view",
    "part:manage",
    "part:archive",
    "material:view",
    "material:manage",
    "material:archive",
    "rfq:view",
    "rfq:create",
    "rfq:change",
    "rfq:archive",
    "rfq:submit",
    "rfq:review",
    "rfq:document_upload",
    "rfq:document_download",
}


def migrate_to(targets):
    executor = MigrationExecutor(connection)
    executor.migrate(targets)
    return MigrationExecutor(connection)


@pytest.mark.django_db(transaction=True)
def test_phase3b_clean_migration_creates_all_owned_tables():
    try:
        migrate_to(BEFORE_PHASE3B)
        migrate_to(AFTER_PHASE3B)
        table_names = set(connection.introspection.table_names())

        assert {
            "business_materials",
            "business_number_sequences",
            "sales_rfqs",
            "sales_rfq_lines",
            "sales_rfq_documents",
            "sales_technical_reviews",
        }.issubset(table_names)
    finally:
        migrate_to(AFTER_PHASE3B)


@pytest.mark.django_db(transaction=True)
def test_phase3b_existing_rows_remain_legacy_and_unchanged():
    try:
        old_executor = migrate_to(BEFORE_PHASE3B)
        old_apps = old_executor.loader.project_state(BEFORE_PHASE3B).apps
        customer_model = old_apps.get_model("business_core", "BusinessCustomer")
        product_model = old_apps.get_model("business_core", "BusinessProduct")

        customer = customer_model.objects.create(
            legacy_customer_id=7101,
            company_name="Historic Buyer",
            contact_name="Historic Contact",
            status="active",
        )
        product = product_model.objects.create(
            legacy_product_id=8101,
            name="Historic Product",
            slug="historic-product-phase3b",
            status="draft",
        )

        new_executor = migrate_to(AFTER_PHASE3B)
        new_apps = new_executor.loader.project_state(AFTER_PHASE3B).apps
        new_customer_model = new_apps.get_model("business_core", "BusinessCustomer")
        new_product_model = new_apps.get_model("business_core", "BusinessProduct")
        migrated_customer = new_customer_model.objects.get(pk=customer.pk)
        migrated_product = new_product_model.objects.get(pk=product.pk)

        assert migrated_customer.legacy_customer_id == 7101
        assert migrated_customer.company_name == "Historic Buyer"
        assert migrated_customer.status == "active"
        assert migrated_customer.data_contract == "LEGACY"
        assert migrated_customer.customer_code is None
        assert migrated_product.legacy_product_id == 8101
        assert migrated_product.name == "Historic Product"
        assert migrated_product.status == "draft"
        assert migrated_product.data_contract == "LEGACY"
        assert migrated_product.part_code is None
    finally:
        migrate_to(AFTER_PHASE3B)


@pytest.mark.django_db(transaction=True)
def test_phase3b_permissions_are_definitions_without_grants():
    try:
        migrate_to(BEFORE_PHASE3B)
        executor = migrate_to(AFTER_PHASE3B)
        apps = executor.loader.project_state(AFTER_PHASE3B).apps
        permission_model = apps.get_model("foundation", "FoundationPermission")
        relation_model = apps.get_model("foundation", "FoundationRolePermission")
        permissions = permission_model.objects.filter(code__in=PHASE3B_PERMISSION_CODES)

        assert set(permissions.values_list("code", flat=True)) == PHASE3B_PERMISSION_CODES
        assert relation_model.objects.filter(permission__in=permissions).count() == 0
    finally:
        migrate_to(AFTER_PHASE3B)


def test_phase3b_migrations_do_not_access_external_legacy_database():
    backend_root = Path(__file__).resolve().parents[1]
    migration_paths = [
        backend_root / "apps/foundation/migrations/0007_define_phase3b_permissions.py",
        backend_root / "apps/business_core/migrations/0003_businessmaterial_businessnumbersequence_and_more.py",
        backend_root / "apps/business_core/migrations/0004_mark_existing_master_rows_legacy.py",
        backend_root / "apps/business_core/migrations/0005_phase3b_master_constraints.py",
        backend_root / "apps/sales/migrations/0002_salesrfq_salesrfqline_salesrfqdocument_and_more.py",
    ]

    forbidden_tokens = ("LEGACY_DATABASE", '.using("legacy")', ".using('legacy')")
    for path in migration_paths:
        migration_source = path.read_text(encoding="utf-8")
        assert all(token not in migration_source for token in forbidden_tokens)
