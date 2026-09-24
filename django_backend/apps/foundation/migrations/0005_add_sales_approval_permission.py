"""Add a dedicated quotation approval permission."""

from django.db import migrations


def add_sales_approval_permission(apps, schema_editor):
    """Allow only the administrator role to approve quotations by default."""
    permission_model = apps.get_model("foundation", "FoundationPermission")
    role_model = apps.get_model("foundation", "FoundationRole")
    relation_model = apps.get_model("foundation", "FoundationRolePermission")

    permission, _created = permission_model.objects.get_or_create(
        code="sales:approve",
        defaults={
            "module": "sales",
            "action": "approve",
            "description": "Allow human approval of managed sales quotations",
        },
    )
    admin_role = role_model.objects.filter(name="admin").first()
    if admin_role:
        relation_model.objects.get_or_create(role=admin_role, permission=permission)


def remove_sales_approval_permission(apps, schema_editor):
    """Remove the role link and permission created by this migration."""
    permission_model = apps.get_model("foundation", "FoundationPermission")
    permission_model.objects.filter(code="sales:approve").delete()


class Migration(migrations.Migration):
    dependencies = [("foundation", "0004_seed_sales_crm_permissions")]  # noqa: RUF012

    operations = [  # noqa: RUF012
        migrations.RunPython(
            add_sales_approval_permission, remove_sales_approval_permission
        ),
    ]
