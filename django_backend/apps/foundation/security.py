"""Central security policies for foundation authentication."""

from __future__ import annotations

import hashlib
import re
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from .models import FoundationLoginAttempt


def privacy_hash(value):
    """Hash identifiers before writing security audit events."""
    normalized = str(value or "").strip().casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest() if normalized else ""


class PasswordPolicy:
    """Validate passwords without storing or logging their plaintext value."""

    def validate(self, password):
        """Require length and a mix of common character classes."""
        minimum = int(getattr(settings, "AUTH_PASSWORD_MIN_LENGTH", 12))
        checks = (
            (
                len(password or "") >= minimum,
                f"Password must contain at least {minimum} characters.",
            ),
            (
                bool(re.search(r"[A-Z]", password or "")),
                "Password must include an uppercase letter.",
            ),
            (
                bool(re.search(r"[a-z]", password or "")),
                "Password must include a lowercase letter.",
            ),
            (bool(re.search(r"\d", password or "")), "Password must include a number."),
            (
                bool(re.search(r"[^A-Za-z0-9]", password or "")),
                "Password must include a symbol.",
            ),
        )
        errors = [message for valid, message in checks if not valid]
        if errors:
            raise ValidationError(errors)


class LoginProtectionService:
    """Apply distributed-cache throttling plus database-backed login auditing."""

    def _window_start(self):
        seconds = int(getattr(settings, "AUTH_LOGIN_WINDOW_SECONDS", 900))
        return timezone.now() - timedelta(seconds=seconds)

    def _attempts(self, email, remote_addr):
        query = FoundationLoginAttempt.objects.filter(
            success=False,
            created_at__gte=self._window_start(),
        )
        email_hash = privacy_hash(email)
        remote_hash = privacy_hash(remote_addr)
        if remote_hash:
            query = query.filter(email_hash=email_hash, remote_addr_hash=remote_hash)
        else:
            query = query.filter(email_hash=email_hash)
        return query.count()

    def enforce(self, email, remote_addr):
        """Reject repeated failures before password hashing work is performed."""
        limit = int(getattr(settings, "AUTH_LOGIN_MAX_FAILURES", 5))
        if self._attempts(email, remote_addr) >= limit:
            self.record(email, remote_addr, False, "locked")
            raise PermissionDenied("Login temporarily locked. Try again later.")

    def record(self, email, remote_addr, success, reason):
        """Persist only hashed identifiers and a bounded reason code."""
        return FoundationLoginAttempt.objects.create(
            email_hash=privacy_hash(email),
            remote_addr_hash=privacy_hash(remote_addr),
            success=bool(success),
            reason=str(reason or "")[:80],
        )
