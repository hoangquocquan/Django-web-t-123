"""Define Phase 3B master-data and RFQ permissions without granting them."""

from django.db import migrations


PERMISSIONS = {
    "customer": ("view", "create", "change", "archive"),
    "part": ("view", "manage", "archive"),
    "material": ("view", "manage", "archive"),
    "rfq": (
        "view",
        "create",
        "change",
        "archive",
        "submit",
        "review",
        "document_upload",
        "document_download",
    ),
}


def description_for(module, action):
    """Return the marker used to identify rows created by this migration."""
    return f"Phase 3B definition: allow {action} on {module}"


def define_permissions(apps, schema_editor):
    """Idempotently create definitions; deliberately create no role grants."""
    permission_model = apps.get_model("foundation", "FoundationPermission")
    db_alias = schema_editor.connection.alias
    for module, actions in PERMISSIONS.items():
        for action in actions:
            permission_model.objects.using(db_alias).get_or_create(
                code=f"{module}:{action}",
                defaults={
                    "module": module,
                    "action": action,
                    "description": description_for(module, action),
                },
            )


def remove_unreferenced_created_permissions(apps, schema_editor):
    """Remove only ungranted rows carrying this migration's exact marker."""
    permission_model = apps.get_model("foundation", "FoundationPermission")
    relation_model = apps.get_model("foundation", "FoundationRolePermission")
    db_alias = schema_editor.connection.alias
    for module, actions in PERMISSIONS.items():
        for action in actions:
            permission = permission_model.objects.using(db_alias).filter(
                code=f"{module}:{action}",
                module=module,
                action=action,
                description=description_for(module, action),
            ).first()
            if permission and not relation_model.objects.using(db_alias).filter(
                permission=permission
            ).exists():
                permission.delete(using=db_alias)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0006_add_login_audit_and_two_factor_challenges")]

    operations = [
        migrations.RunPython(
            define_permissions,
            remove_unreferenced_created_permissions,
        ),
    ]
