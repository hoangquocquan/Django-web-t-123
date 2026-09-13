"""Define Phase 3D actions and grant the approved canonical role matrix."""

from django.db import migrations


NEW_PERMISSIONS = {
    "order": ("view", "progress", "hold", "resume", "complete", "cancel"),
    "audit": ("view",),
    "user": ("view", "manage"),
}

ROLE_GRANTS = {
    "Admin": {
        "user:view", "user:manage",
        "customer:view", "customer:create", "customer:change", "customer:archive",
        "part:view", "part:manage", "part:archive",
        "material:view", "material:manage", "material:archive",
        "rfq:view", "rfq:create", "rfq:change", "rfq:archive", "rfq:submit",
        "rfq:document_upload", "rfq:document_download",
        "quotation:view", "quotation:create_revision", "quotation:change",
        "quotation:submit", "quotation:send", "quotation:record_customer_decision",
        "quotation:convert",
        "order:view", "order:progress", "order:hold", "order:resume",
        "order:complete", "order:cancel", "audit:view",
    },
    "Sales": {
        "customer:view", "customer:create", "customer:change", "customer:archive",
        "part:view", "material:view",
        "rfq:view", "rfq:create", "rfq:change", "rfq:archive", "rfq:submit",
        "rfq:document_upload", "rfq:document_download",
        "quotation:view", "quotation:create_revision", "quotation:change",
        "quotation:submit", "quotation:send", "quotation:record_customer_decision",
        "quotation:convert", "order:view",
    },
    "Manager": {
        "customer:view", "part:view", "material:view",
        "rfq:view", "rfq:review", "rfq:document_download",
        "quotation:view", "quotation:approve", "quotation:reject",
        "order:view", "order:progress", "order:hold", "order:resume",
        "order:complete", "order:cancel", "audit:view",
    },
}


def permission_marker(module, action):
    return f"Phase 3D definition: allow {action} on {module}"


def role_marker(role_name):
    return f"Phase 3D canonical role: {role_name}"


def seed_phase3d_rbac(apps, schema_editor):
    permission_model = apps.get_model("foundation", "FoundationPermission")
    role_model = apps.get_model("foundation", "FoundationRole")
    relation_model = apps.get_model("foundation", "FoundationRolePermission")
    db_alias = schema_editor.connection.alias

    required_codes = set().union(*ROLE_GRANTS.values())
    for code in sorted(required_codes):
        module, action = code.split(":", 1)
        permission, _created = permission_model.objects.using(db_alias).get_or_create(
            code=code,
            defaults={
                "module": module,
                "action": action,
                "description": permission_marker(module, action),
            },
        )
        if permission.module != module or permission.action != action:
            raise RuntimeError(f"BLOCKED_PHASE_3D_PERMISSION_COLLISION: {code}")

    for role_name, grant_codes in ROLE_GRANTS.items():
        role, _created = role_model.objects.using(db_alias).get_or_create(
            name=role_name,
            defaults={"description": role_marker(role_name)},
        )
        permissions = {
            item.code: item
            for item in permission_model.objects.using(db_alias).filter(code__in=grant_codes)
        }
        missing = sorted(grant_codes - set(permissions))
        if missing:
            raise RuntimeError(
                "BLOCKED_PHASE_3D_PERMISSION_DEFINITION: " + ", ".join(missing)
            )
        for code in sorted(grant_codes):
            relation_model.objects.using(db_alias).get_or_create(
                role=role,
                permission=permissions[code],
            )


def reverse_phase3d_rbac(apps, schema_editor):
    permission_model = apps.get_model("foundation", "FoundationPermission")
    role_model = apps.get_model("foundation", "FoundationRole")
    relation_model = apps.get_model("foundation", "FoundationRolePermission")
    user_model = apps.get_model("foundation", "FoundationUser")
    db_alias = schema_editor.connection.alias

    for role_name in ROLE_GRANTS:
        role = role_model.objects.using(db_alias).filter(
            name=role_name,
            description=role_marker(role_name),
        ).first()
        if not role:
            continue
        if user_model.objects.using(db_alias).filter(role=role).exists():
            raise RuntimeError("FORWARD_FIX_REQUIRED_PHASE3D_RBAC_HAS_USERS")
        relation_model.objects.using(db_alias).filter(role_id=role.pk)._raw_delete(db_alias)
        role_model.objects.using(db_alias).filter(pk=role.pk)._raw_delete(db_alias)

    for module, actions in NEW_PERMISSIONS.items():
        for action in actions:
            permission = permission_model.objects.using(db_alias).filter(
                code=f"{module}:{action}",
                module=module,
                action=action,
                description=permission_marker(module, action),
            ).first()
            if permission and not relation_model.objects.using(db_alias).filter(
                permission=permission
            ).exists():
                permission_model.objects.using(db_alias).filter(pk=permission.pk)._raw_delete(db_alias)


class Migration(migrations.Migration):
    dependencies = [
        ("foundation", "0008_define_phase3c_permissions"),
        ("transaction_domain", "0004_classify_phase3d_legacy_orders"),
    ]

    operations = [migrations.RunPython(seed_phase3d_rbac, reverse_phase3d_rbac)]
