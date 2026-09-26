"""Define and grant the narrow permissions used by the LINE UAT demo."""

# ruff: noqa: RUF012 - Django migration class attributes are declarative.

from django.db import migrations

PERMISSIONS = {
    "line_uat:read": ("line_uat", "read"),
    "line_uat:approve": ("line_uat", "approve"),
}


def grant_line_uat_permissions(apps, schema_editor):
    permission_model = apps.get_model("foundation", "FoundationPermission")
    role_model = apps.get_model("foundation", "FoundationRole")
    relation_model = apps.get_model("foundation", "FoundationRolePermission")
    db_alias = schema_editor.connection.alias

    permissions = {}
    for code, (module, action) in PERMISSIONS.items():
        permission, _created = permission_model.objects.using(db_alias).get_or_create(
            code=code,
            defaults={
                "module": module,
                "action": action,
                "description": f"Allow {action} on the synthetic LINE UAT demo",
            },
        )
        permissions[code] = permission

    for role in role_model.objects.using(db_alias).all():
        role_name = role.name.casefold()
        if role_name in {"sales", "manager", "admin"}:
            relation_model.objects.using(db_alias).get_or_create(
                role=role, permission=permissions["line_uat:read"]
            )
        if role_name in {"manager", "admin"}:
            relation_model.objects.using(db_alias).get_or_create(
                role=role, permission=permissions["line_uat:approve"]
            )


def revoke_line_uat_permissions(apps, schema_editor):
    permission_model = apps.get_model("foundation", "FoundationPermission")
    relation_model = apps.get_model("foundation", "FoundationRolePermission")
    db_alias = schema_editor.connection.alias
    permission_ids = list(
        permission_model.objects.using(db_alias)
        .filter(code__in=PERMISSIONS)
        .values_list("pk", flat=True)
    )
    relation_model.objects.using(db_alias).filter(
        permission_id__in=permission_ids
    ).delete()
    permission_model.objects.using(db_alias).filter(pk__in=permission_ids).delete()


class Migration(migrations.Migration):
    dependencies = [("foundation", "0010_phase4c_role_activity_and_quotation_archive")]
    operations = [
        migrations.RunPython(grant_line_uat_permissions, revoke_line_uat_permissions)
    ]
