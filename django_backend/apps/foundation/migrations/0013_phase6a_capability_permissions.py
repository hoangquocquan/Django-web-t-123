"""Define and grant exact Capability CMS permissions without creating roles."""

from django.db import migrations


MODULE = "capabilities"
ACTIONS = ("read", "edit", "review", "approve", "publish", "archive")
ROLE_GRANTS = {
    "editor": {"read", "edit"},
    "Manager": {"read", "review", "approve"},
    "Admin": {"read", "publish", "archive"},
    "viewer": {"read"},
    "Sales": set(),
    "admin": set(),
}


def permission_marker(action):
    return f"Phase 6A definition: allow {action} on Capability CMS"


def apply_capability_permissions(apps, schema_editor):
    permission_model = apps.get_model("foundation", "FoundationPermission")
    role_model = apps.get_model("foundation", "FoundationRole")
    relation_model = apps.get_model("foundation", "FoundationRolePermission")
    db_alias = schema_editor.connection.alias
    roles = {
        role.name: role
        for role in role_model.objects.using(db_alias).filter(name__in=ROLE_GRANTS)
    }
    permissions = {}
    for action in ACTIONS:
        code = f"{MODULE}:{action}"
        permission, _created = permission_model.objects.using(db_alias).get_or_create(
            code=code,
            defaults={
                "module": MODULE,
                "action": action,
                "description": permission_marker(action),
            },
        )
        if permission.module != MODULE or permission.action != action:
            raise RuntimeError(f"BLOCKED_PHASE_6A_PERMISSION_COLLISION: {code}")
        permissions[action] = permission

    for role_name, actions in ROLE_GRANTS.items():
        role = roles.get(role_name)
        if role is None:
            continue
        for action in actions:
            relation_model.objects.using(db_alias).get_or_create(
                role=role,
                permission=permissions[action],
            )


def reverse_capability_permissions(apps, schema_editor):
    permission_model = apps.get_model("foundation", "FoundationPermission")
    role_model = apps.get_model("foundation", "FoundationRole")
    relation_model = apps.get_model("foundation", "FoundationRolePermission")
    db_alias = schema_editor.connection.alias
    role_ids = role_model.objects.using(db_alias).filter(
        name__in=ROLE_GRANTS
    ).values_list("pk", flat=True)
    for action in ACTIONS:
        permission = permission_model.objects.using(db_alias).filter(
            code=f"{MODULE}:{action}",
            module=MODULE,
            action=action,
            description=permission_marker(action),
        ).first()
        if permission is None:
            continue
        relation_model.objects.using(db_alias).filter(
            role_id__in=role_ids,
            permission=permission,
        ).delete()
        if not relation_model.objects.using(db_alias).filter(
            permission=permission
        ).exists():
            permission.delete(using=db_alias)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0012_phase5c_public_product_permissions")]

    operations = [
        migrations.RunPython(
            apply_capability_permissions,
            reverse_capability_permissions,
        )
    ]


