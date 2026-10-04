"""Create one short-lived Foundation token for the isolated LINE UAT runtime."""

from __future__ import annotations

import os
import secrets
import sys
from datetime import timedelta
from pathlib import Path


def configure_django() -> None:
    """Configure Django when the helper runs as a standalone process."""
    repo_root = Path(__file__).resolve().parents[2]
    django_root = repo_root / "django_backend"
    script_root = Path(__file__).resolve().parent
    for path in (django_root, script_root):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

    import django

    django.setup()


def create_temporary_principal():
    """Create a short-lived token only for the exact UAT-scoped manager role."""
    from apps.foundation.models import (
        FoundationAuthToken,
        FoundationRole,
        FoundationUser,
    )
    from apps.foundation.services import FoundationAuthService
    from bootstrap_foundation_uat import (
        REQUIRED_PERMISSIONS,
        ROLE_DESCRIPTION,
        ROLE_NAME,
    )
    from django.utils import timezone

    role = FoundationRole.objects.get(name=ROLE_NAME, description=ROLE_DESCRIPTION)
    granted_codes = set(role.permissions.values_list("code", flat=True))
    if granted_codes != set(REQUIRED_PERMISSIONS):
        raise RuntimeError("SAFETY STOP: UAT manager role is not least-privilege.")
    user, _ = FoundationUser.objects.get_or_create(
        email="line-uat-runtime@example.invalid",
        defaults={
            "full_name": "LINE UAT Runtime",
            "password_hash": "!",
            "role": role,
            "is_active": True,
        },
    )
    if user.role_id != role.id or not user.is_active:
        user.role = role
        user.is_active = True
        user.save(update_fields=["role", "is_active", "updated_at"])

    raw_token = secrets.token_urlsafe(32)
    token = FoundationAuthToken.objects.create(
        user=user,
        token_hash=FoundationAuthService.hash_token(raw_token),
        expires_at=timezone.now() + timedelta(hours=4),
        remote_addr="127.0.0.1",
        user_agent="isolated-line-uat-runtime",
    )
    return raw_token, token


def main() -> int:
    configure_django()
    raw_token, _token = create_temporary_principal()
    # The caller captures stdout directly into memory and never logs this value.
    print(raw_token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
