"""Create one short-lived Foundation token for the isolated LINE UAT runtime."""

from __future__ import annotations

import os
import secrets
import sys
from datetime import timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DJANGO_ROOT = REPO_ROOT / "django_backend"
sys.path.insert(0, str(DJANGO_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

import django

django.setup()

from apps.foundation.models import (
    FoundationAuthToken,
    FoundationRole,
    FoundationUser,
)
from apps.foundation.services import FoundationAuthService
from django.utils import timezone


def main() -> int:
    role = FoundationRole.objects.get(name="manager")
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
    FoundationAuthToken.objects.create(
        user=user,
        token_hash=FoundationAuthService.hash_token(raw_token),
        expires_at=timezone.now() + timedelta(hours=4),
        remote_addr="127.0.0.1",
        user_agent="isolated-line-uat-runtime",
    )
    # The caller captures stdout directly into memory and never logs this value.
    print(raw_token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

