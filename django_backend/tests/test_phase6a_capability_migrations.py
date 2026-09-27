"""Phase 6A Capability schema/permission forward and reverse migration tests."""

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


BEFORE = [
    ("business_core", "0006_aimachiningestimate"),
    ("foundation", "0012_phase5c_public_product_permissions"),
]
AFTER = [
    ("business_core", "0007_capability_publicproductprojection"),
    ("foundation", "0013_phase6a_capability_permissions"),
]
EXPECTED = {
    "editor": {"capabilities:read", "capabilities:edit"},
    "Manager": {
        "capabilities:read",
        "capabilities:review",
        "capabilities:approve",
    },
    "Admin": {
        "capabilities:read",
        "capabilities:publish",
        "capabilities:archive",
    },
    "viewer": {"capabilities:read"},
    "Sales": set(),
    "admin": set(),
}


def migrate_to(targets):
    executor = MigrationExecutor(connection)
    executor.migrate(targets)
    return MigrationExecutor(connection)


@pytest.mark.django_db(transaction=True)
def test_capability_schema_permissions_and_safe_reverse():
    try:
        before_executor = migrate_to(BEFORE)
        before_apps = before_executor.loader.project_state(BEFORE).apps
        role_model = before_apps.get_model("foundation", "FoundationRole")
        for role_name in EXPECTED:
            role_model.objects.get_or_create(name=role_name)

        executor = migrate_to(AFTER)
        apps = executor.loader.project_state(AFTER).apps
        capability_model = apps.get_model("business_core", "Capability")
        permission_model = apps.get_model("foundation", "FoundationPermission")
        role_model = apps.get_model("foundation", "FoundationRole")
        assert capability_model.objects.count() == 0
        assert permission_model.objects.filter(module="capabilities").count() == 6
        for role_name, codes in EXPECTED.items():
            assert set(
                role_model.objects.get(name=role_name)
                .permissions.filter(module="capabilities")
                .values_list("code", flat=True)
            ) == codes

        reverse_executor = migrate_to(BEFORE)
        reverse_apps = reverse_executor.loader.project_state(BEFORE).apps
        assert not reverse_apps.get_model(
            "foundation", "FoundationPermission"
        ).objects.filter(module="capabilities").exists()
        assert "Capability" not in {
            model.__name__
            for model in reverse_apps.get_models()
            if model._meta.app_label == "business_core"
        }
        assert set(
            reverse_apps.get_model("foundation", "FoundationRole")
            .objects.filter(name__in=EXPECTED)
            .values_list("name", flat=True)
        ) == set(EXPECTED)
    finally:
        migrate_to(AFTER)


