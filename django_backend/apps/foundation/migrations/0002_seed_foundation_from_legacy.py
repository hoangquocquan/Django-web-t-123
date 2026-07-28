"""Seed Django-owned foundation data from the legacy admin tables."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from django.contrib.auth.hashers import make_password
from django.db import migrations


FOUNDATION_MODULES = [
    "dashboard",
    "products",
    "categories",
    "news",
    "media",
    "pages",
    "menus",
    "banners",
    "contacts",
    "quotes",
    "customers",
    "newsletter",
    "ai",
    "developer",
    "users",
    "permissions",
    "auth",
]


ROLE_MATRIX = {
    "admin": {"*": ["*"]},
    "editor": {module: ["read", "write"] for module in FOUNDATION_MODULES if module not in {"users", "permissions"}},
    "viewer": {"*": ["read"]},
}


def _project_root():
    """Return the repository root from this migration file."""
    return Path(__file__).resolve().parents[4]


def _legacy_database_path():
    """Return the expected legacy SQLite database path."""
    return _project_root() / "backend" / "database" / "mecprecision.sqlite"


def _iter_legacy_admin_users():
    """Read legacy admin users directly in read-only SQLite mode."""
    database_path = _legacy_database_path()
    if not database_path.exists():
        return []

    connection_uri = f"file:{database_path.as_posix()}?mode=ro"
    with sqlite3.connect(connection_uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                id,
                full_name,
                email,
                password_hash,
                role,
                is_active,
                avatar_url,
                two_factor_enabled
            FROM admin_users
            ORDER BY id
            """
        ).fetchall()
        return [dict(row) for row in rows]


def _create_permission(apps, module, action):
    """Create or reuse one permission row."""
    FoundationPermission = apps.get_model("foundation", "FoundationPermission")
    code = f"{module}:{action}"
    permission, _created = FoundationPermission.objects.get_or_create(
        code=code,
        defaults={
            "module": module,
            "action": action,
            "description": f"Allow {action} on {module}",
        },
    )
    return permission


def _seed_roles_and_permissions(apps):
    """Create foundation roles and attach their permission matrix."""
    FoundationRole = apps.get_model("foundation", "FoundationRole")
    FoundationRolePermission = apps.get_model("foundation", "FoundationRolePermission")

    roles = {}
    for role_name, permissions in ROLE_MATRIX.items():
        role, _created = FoundationRole.objects.get_or_create(
            name=role_name,
            defaults={"description": f"Foundation {role_name} role migrated from legacy CMS"},
        )
        roles[role_name] = role
        for module, actions in permissions.items():
            for action in actions:
                permission = _create_permission(apps, module, action)
                FoundationRolePermission.objects.get_or_create(role=role, permission=permission)
    return roles


def _safe_password_hash(legacy_hash):
    """Keep supported Django hashes and disable unsupported legacy hashes."""
    if str(legacy_hash or "").startswith("pbkdf2_sha256$"):
        return legacy_hash
    return make_password(None)


def seed_foundation_data(apps, schema_editor):
    """Seed roles, permissions, users, and profiles without changing legacy tables."""
    FoundationUser = apps.get_model("foundation", "FoundationUser")
    FoundationUserProfile = apps.get_model("foundation", "FoundationUserProfile")
    roles = _seed_roles_and_permissions(apps)

    for legacy_user in _iter_legacy_admin_users():
        role = roles.get(legacy_user.get("role")) or roles["viewer"]
        user, created = FoundationUser.objects.update_or_create(
            legacy_admin_id=legacy_user["id"],
            defaults={
                "email": legacy_user["email"],
                "full_name": legacy_user["full_name"],
                "password_hash": _safe_password_hash(legacy_user["password_hash"]),
                "role": role,
                "is_active": bool(legacy_user["is_active"]),
            },
        )
        profile_defaults = {
            "avatar_url": legacy_user.get("avatar_url") or "",
            "two_factor_enabled": bool(legacy_user.get("two_factor_enabled")),
        }
        if created:
            FoundationUserProfile.objects.create(user=user, **profile_defaults)
        else:
            FoundationUserProfile.objects.update_or_create(user=user, defaults=profile_defaults)


def noop_reverse(apps, schema_editor):
    """Keep seeded data during rollback to avoid accidental data loss."""


class Migration(migrations.Migration):

    dependencies = [
        ("foundation", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_foundation_data, noop_reverse),
    ]
