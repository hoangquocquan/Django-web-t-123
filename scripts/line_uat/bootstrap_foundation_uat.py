"""Bootstrap the least-privilege Foundation role for isolated LINE UAT."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROLE_NAME = "manager"
ROLE_DESCRIPTION = "Isolated LINE UAT manager role (minimum permissions only)"
REQUIRED_PERMISSIONS = {
    "ai_sales:read": ("ai_sales", "read"),
    "sales:read": ("sales", "read"),
    "line_uat:read": ("line_uat", "read"),
    "line_uat:approve": ("line_uat", "approve"),
}


def configure_django() -> None:
    """Configure Django when the helper runs as a standalone process."""
    repo_root = Path(__file__).resolve().parents[2]
    django_root = repo_root / "django_backend"
    if str(django_root) not in sys.path:
        sys.path.insert(0, str(django_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

    import django

    django.setup()


def bootstrap_uat_role():
    """Create or verify one exact, idempotent, least-privilege UAT role."""
    from apps.foundation.models import (
        FoundationPermission,
        FoundationRole,
        FoundationRolePermission,
    )
    from django.db import transaction

    with transaction.atomic():
        role, created = FoundationRole.objects.get_or_create(
            name=ROLE_NAME,
            defaults={"description": ROLE_DESCRIPTION, "is_active": True},
        )
        if not created and role.description != ROLE_DESCRIPTION:
            raise RuntimeError("SAFETY STOP: existing lowercase manager role is not UAT-owned.")
        if not role.is_active:
            role.is_active = True
            role.save(update_fields=["is_active"])

        for code, (module, action) in REQUIRED_PERMISSIONS.items():
            try:
                permission = FoundationPermission.objects.get(code=code)
            except FoundationPermission.DoesNotExist as exc:
                raise RuntimeError(
                    f"SAFETY STOP: migration-defined permission is missing: {code}"
                ) from exc
            if permission.module != module or permission.action != action:
                raise RuntimeError(
                    f"SAFETY STOP: permission definition collision: {code}"
                )
            FoundationRolePermission.objects.get_or_create(
                role=role,
                permission=permission,
            )

        granted_codes = set(role.permissions.values_list("code", flat=True))
        required_codes = set(REQUIRED_PERMISSIONS)
        if granted_codes != required_codes:
            extra = sorted(granted_codes - required_codes)
            missing = sorted(required_codes - granted_codes)
            raise RuntimeError(
                "SAFETY STOP: UAT role permission scope mismatch; "
                f"extra={extra!r}; missing={missing!r}"
            )
        return role


def main() -> int:
    configure_django()
    bootstrap_uat_role()
    print("FOUNDATION_UAT_ROLE_READY=yes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
