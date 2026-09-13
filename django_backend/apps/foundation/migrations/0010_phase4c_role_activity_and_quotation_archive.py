"""Add enforceable role activity and the Phase 4C quotation archive grant."""

from django.db import migrations, models


PERMISSION_CODE = "quotation:archive"
PERMISSION_MARKER = "Phase 4C definition: allow archive on quotation"
ROLE_NAMES = ("Admin", "Sales")


def seed_quotation_archive_permission(apps, schema_editor):
    permission_model = apps.get_model("foundation", "FoundationPermission")
    role_model = apps.get_model("foundation", "FoundationRole")
    relation_model = apps.get_model("foundation", "FoundationRolePermission")
    db_alias = schema_editor.connection.alias

    permission, _created = permission_model.objects.using(db_alias).get_or_create(
        code=PERMISSION_CODE,
        defaults={
            "module": "quotation",
            "action": "archive",
            "description": PERMISSION_MARKER,
        },
    )
    if permission.module != "quotation" or permission.action != "archive":
        raise RuntimeError("BLOCKED_PHASE_4C_PERMISSION_COLLISION: quotation:archive")
    for role in role_model.objects.using(db_alias).filter(name__in=ROLE_NAMES):
        relation_model.objects.using(db_alias).get_or_create(
            role=role,
            permission=permission,
        )


def remove_phase4c_archive_grants(apps, schema_editor):
    permission_model = apps.get_model("foundation", "FoundationPermission")
    role_model = apps.get_model("foundation", "FoundationRole")
    relation_model = apps.get_model("foundation", "FoundationRolePermission")
    db_alias = schema_editor.connection.alias

    permission = permission_model.objects.using(db_alias).filter(
        code=PERMISSION_CODE,
        module="quotation",
        action="archive",
        description=PERMISSION_MARKER,
    ).first()
    if permission is None:
        return
    role_ids = role_model.objects.using(db_alias).filter(
        name__in=ROLE_NAMES
    ).values_list("pk", flat=True)
    relation_model.objects.using(db_alias).filter(
        role_id__in=role_ids,
        permission=permission,
    ).delete()
    if not relation_model.objects.using(db_alias).filter(permission=permission).exists():
        permission.delete(using=db_alias)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0009_seed_phase3d_rbac")]

    operations = [
        migrations.AddField(
            model_name="foundationrole",
            name="is_active",
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.RunPython(
            seed_quotation_archive_permission,
            remove_phase4c_archive_grants,
        ),
    ]
