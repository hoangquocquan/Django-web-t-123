"""Define Phase 3C quotation permissions without granting them."""

from django.db import migrations


ACTIONS = (
    "view",
    "create_revision",
    "change",
    "submit",
    "approve",
    "reject",
    "send",
    "record_customer_decision",
    "convert",
)


def description_for(action):
    return f"Phase 3C definition: allow {action} on quotation"


def define_permissions(apps, schema_editor):
    permission_model = apps.get_model("foundation", "FoundationPermission")
    db_alias = schema_editor.connection.alias
    for action in ACTIONS:
        permission_model.objects.using(db_alias).get_or_create(
            code=f"quotation:{action}",
            defaults={
                "module": "quotation",
                "action": action,
                "description": description_for(action),
            },
        )


def remove_unreferenced_created_permissions(apps, schema_editor):
    permission_model = apps.get_model("foundation", "FoundationPermission")
    relation_model = apps.get_model("foundation", "FoundationRolePermission")
    db_alias = schema_editor.connection.alias
    for action in ACTIONS:
        permission = permission_model.objects.using(db_alias).filter(
            code=f"quotation:{action}",
            module="quotation",
            action=action,
            description=description_for(action),
        ).first()
        if permission and not relation_model.objects.using(db_alias).filter(
            permission=permission
        ).exists():
            permission.delete(using=db_alias)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0007_define_phase3b_permissions")]

    operations = [
        migrations.RunPython(
            define_permissions,
            remove_unreferenced_created_permissions,
        )
    ]
