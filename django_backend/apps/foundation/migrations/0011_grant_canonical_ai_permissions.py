"""Grant bounded AI capabilities to the canonical Phase 6 roles."""

from django.db import migrations


ROLE_GRANTS = {
    "Admin": {"ai_sales:read", "knowledge:read", "knowledge:write"},
    "Sales": {"ai_sales:read", "knowledge:read"},
    "Manager": {"knowledge:read"},
}


def grant_canonical_ai_permissions(apps, schema_editor):
    permission_model = apps.get_model("foundation", "FoundationPermission")
    role_model = apps.get_model("foundation", "FoundationRole")
    relation_model = apps.get_model("foundation", "FoundationRolePermission")
    db_alias = schema_editor.connection.alias

    for role_name, permission_codes in ROLE_GRANTS.items():
        role = role_model.objects.using(db_alias).filter(name=role_name).first()
        if role is None:
            continue
        for code in sorted(permission_codes):
            module, action = code.split(":", 1)
            permission, _created = permission_model.objects.using(
                db_alias
            ).get_or_create(
                code=code,
                defaults={
                    "module": module,
                    "action": action,
                    "description": f"Canonical AI grant: allow {action} on {module}",
                },
            )
            if permission.module != module or permission.action != action:
                raise RuntimeError(f"CANONICAL_AI_PERMISSION_COLLISION: {code}")
            relation_model.objects.using(db_alias).get_or_create(
                role=role,
                permission=permission,
            )


def revoke_canonical_ai_permissions(apps, schema_editor):
    permission_model = apps.get_model("foundation", "FoundationPermission")
    role_model = apps.get_model("foundation", "FoundationRole")
    relation_model = apps.get_model("foundation", "FoundationRolePermission")
    db_alias = schema_editor.connection.alias

    for role_name, permission_codes in ROLE_GRANTS.items():
        role = role_model.objects.using(db_alias).filter(name=role_name).first()
        if role is None:
            continue
        permission_ids = permission_model.objects.using(db_alias).filter(
            code__in=permission_codes
        ).values_list("id", flat=True)
        relation_model.objects.using(db_alias).filter(
            role=role,
            permission_id__in=permission_ids,
        ).delete()


class Migration(migrations.Migration):
    dependencies = [("foundation", "0010_phase4c_role_activity_and_quotation_archive")]

    operations = [
        migrations.RunPython(
            grant_canonical_ai_permissions,
            revoke_canonical_ai_permissions,
        )
    ]
