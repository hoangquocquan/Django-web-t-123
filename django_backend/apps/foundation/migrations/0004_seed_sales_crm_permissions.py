"""Add Sales CRM AI platform permissions."""

from django.db import migrations


PERMISSIONS = [
    ("sales", "read"),
    ("sales", "write"),
    ("crm", "read"),
    ("crm", "write"),
    ("ai_sales", "read"),
    ("ai_sales", "write"),
]


def seed_sales_crm_permissions(apps, schema_editor):
    """Create sales/CRM permissions and attach them to foundation roles."""
    FoundationPermission = apps.get_model("foundation", "FoundationPermission")
    FoundationRole = apps.get_model("foundation", "FoundationRole")
    FoundationRolePermission = apps.get_model("foundation", "FoundationRolePermission")

    created_permissions = {}
    for module, action in PERMISSIONS:
        permission, _created = FoundationPermission.objects.get_or_create(
            code=f"{module}:{action}",
            defaults={
                "module": module,
                "action": action,
                "description": f"Allow {action} on {module}",
            },
        )
        created_permissions[(module, action)] = permission

    for role_name in ["admin", "editor"]:
        try:
            role = FoundationRole.objects.get(name=role_name)
        except FoundationRole.DoesNotExist:
            continue
        for permission in created_permissions.values():
            FoundationRolePermission.objects.get_or_create(role=role, permission=permission)

    try:
        viewer = FoundationRole.objects.get(name="viewer")
    except FoundationRole.DoesNotExist:
        return
    for key in [("sales", "read"), ("crm", "read"), ("ai_sales", "read")]:
        FoundationRolePermission.objects.get_or_create(role=viewer, permission=created_permissions[key])


def noop_reverse(apps, schema_editor):
    """Keep permissions during rollback to avoid accidental access churn."""


class Migration(migrations.Migration):

    dependencies = [
        ("foundation", "0003_seed_ai_platform_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_sales_crm_permissions, noop_reverse),
    ]
