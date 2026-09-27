"""Phase 5C Public Product permission migration and rollback tests."""

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


BEFORE_PHASE5C = [("foundation", "0010_phase4c_role_activity_and_quotation_archive")]
AFTER_PHASE5C = [("foundation", "0012_phase5c_public_product_permissions")]
EXPECTED = {
    "editor": {"public_products:read", "public_products:edit"},
    "Manager": {
        "public_products:read",
        "public_products:review",
        "public_products:approve",
    },
    "Admin": {
        "public_products:read",
        "public_products:publish",
        "public_products:archive",
    },
    "viewer": {"public_products:read"},
    "Sales": set(),
    "admin": set(),
}


def migrate_to(targets):
    executor = MigrationExecutor(connection)
    executor.migrate(targets)
    return MigrationExecutor(connection)


@pytest.mark.django_db(transaction=True)
def test_phase5c_permission_mapping_and_safe_reverse():
    try:
        before_executor = migrate_to(BEFORE_PHASE5C)
        before_apps = before_executor.loader.project_state(BEFORE_PHASE5C).apps
        before_role_model = before_apps.get_model("foundation", "FoundationRole")
        for role_name in EXPECTED:
            before_role_model.objects.get_or_create(
                name=role_name,
                defaults={"description": "Phase 5C migration test fixture"},
            )
        executor = migrate_to(AFTER_PHASE5C)
        apps = executor.loader.project_state(AFTER_PHASE5C).apps
        permission_model = apps.get_model("foundation", "FoundationPermission")
        role_model = apps.get_model("foundation", "FoundationRole")
        permissions = permission_model.objects.filter(module="public_products")
        assert set(permissions.values_list("code", flat=True)) == {
            f"public_products:{action}"
            for action in ("read", "edit", "review", "approve", "publish", "archive")
        }
        for role_name, expected in EXPECTED.items():
            role = role_model.objects.get(name=role_name)
            assert set(
                role.permissions.filter(module="public_products").values_list(
                    "code", flat=True
                )
            ) == expected

        reverse_executor = migrate_to(BEFORE_PHASE5C)
        reverse_apps = reverse_executor.loader.project_state(BEFORE_PHASE5C).apps
        reverse_permission_model = reverse_apps.get_model(
            "foundation", "FoundationPermission"
        )
        reverse_role_model = reverse_apps.get_model("foundation", "FoundationRole")
        assert reverse_permission_model.objects.filter(
            module="public_products"
        ).count() == 0
        assert set(
            reverse_role_model.objects.filter(name__in=EXPECTED).values_list(
                "name", flat=True
            )
        ) == set(EXPECTED)
    finally:
        migrate_to(AFTER_PHASE5C)


@pytest.mark.django_db(transaction=True)
def test_phase5c_clean_database_does_not_create_roles():
    try:
        before_executor = migrate_to(BEFORE_PHASE5C)
        before_apps = before_executor.loader.project_state(BEFORE_PHASE5C).apps
        role_model = before_apps.get_model("foundation", "FoundationRole")
        role_model.objects.filter(name__in=EXPECTED).delete()

        executor = migrate_to(AFTER_PHASE5C)
        apps = executor.loader.project_state(AFTER_PHASE5C).apps
        permission_model = apps.get_model("foundation", "FoundationPermission")
        role_model = apps.get_model("foundation", "FoundationRole")
        assert permission_model.objects.filter(module="public_products").count() == 6
        assert not role_model.objects.filter(name__in=EXPECTED).exists()
    finally:
        migrate_to(AFTER_PHASE5C)


