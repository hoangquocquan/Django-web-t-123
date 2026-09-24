"""Add AI platform permissions for RAG and agent modules."""

from django.db import migrations


AI_PLATFORM_PERMISSIONS = [
    ("knowledge", "read"),
    ("knowledge", "write"),
    ("agent", "read"),
    ("agent", "write"),
]


def seed_ai_platform_permissions(apps, schema_editor):
    """Create permissions and attach write access to admin/editor roles."""
    FoundationPermission = apps.get_model("foundation", "FoundationPermission")
    FoundationRole = apps.get_model("foundation", "FoundationRole")
    FoundationRolePermission = apps.get_model("foundation", "FoundationRolePermission")

    permissions = {}
    for module, action in AI_PLATFORM_PERMISSIONS:
        permission, _created = FoundationPermission.objects.get_or_create(
            code=f"{module}:{action}",
            defaults={
                "module": module,
                "action": action,
                "description": f"Allow {action} on {module}",
            },
        )
        permissions[(module, action)] = permission

    for role_name in ["admin", "editor"]:
        try:
            role = FoundationRole.objects.get(name=role_name)
        except FoundationRole.DoesNotExist:
            continue
        for permission in permissions.values():
            FoundationRolePermission.objects.get_or_create(role=role, permission=permission)

    try:
        viewer = FoundationRole.objects.get(name="viewer")
    except FoundationRole.DoesNotExist:
        return
    for key in [("knowledge", "read"), ("agent", "read")]:
        FoundationRolePermission.objects.get_or_create(role=viewer, permission=permissions[key])


def noop_reverse(apps, schema_editor):
    """Keep permissions on rollback to avoid accidental access churn."""


class Migration(migrations.Migration):

    dependencies = [
        ("foundation", "0002_seed_foundation_from_legacy"),
    ]

    operations = [
        migrations.RunPython(seed_ai_platform_permissions, noop_reverse),
    ]

