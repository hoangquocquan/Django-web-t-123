"""Service layer for Django-owned authentication, users, and permissions."""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    FoundationAuthToken,
    FoundationPermission,
    FoundationRole,
    FoundationUser,
    FoundationUserProfile,
)


TOKEN_TTL_HOURS = 8


class FoundationPermissionService:
    """Own role and permission decisions in Django."""

    def permissions_for_role(self, role):
        """Return a serializable permission map for one role."""
        permissions = role.permissions.all()
        result = {}
        for permission in permissions:
            result.setdefault(permission.module, []).append(permission.action)
        return {module: sorted(actions) for module, actions in result.items()}

    def has_permission(self, user, module, action="read"):
        """Return whether a user can perform an action."""
        if not user or not user.is_active:
            return False
        role = user.role
        if role.permissions.filter(module="*", action=action).exists():
            return True
        if role.permissions.filter(module="*", action="*").exists():
            return True
        return role.permissions.filter(module=module, action=action).exists()

    def require_permission(self, user, module, action="read"):
        """Raise when a user lacks a permission."""
        if not self.has_permission(user, module, action):
            raise PermissionDenied(f"Missing permission: {module}:{action}")


class FoundationUserService:
    """Own user and profile writes in Django."""

    def list_users(self):
        """Return Django-owned users with role/profile loaded."""
        return FoundationUser.objects.select_related("role", "profile").all()

    def get_user(self, user_id):
        """Return one Django-owned user."""
        return self.list_users().get(id=user_id)

    @transaction.atomic
    def create_user(self, email, full_name, password, role_name="viewer", profile=None):
        """Create a Django-owned user and profile."""
        if not password:
            raise ValidationError("Password is required.")
        if FoundationUser.objects.filter(email=email).exists():
            raise ValidationError("Email already exists.")
        try:
            role = FoundationRole.objects.get(name=role_name)
        except FoundationRole.DoesNotExist as exc:
            raise ValidationError("Role does not exist.") from exc
        user = FoundationUser.objects.create(
            email=email,
            full_name=full_name,
            password_hash=make_password(password),
            role=role,
        )
        FoundationUserProfile.objects.create(user=user, **(profile or {}))
        return user

    @transaction.atomic
    def update_profile(self, user, **profile_fields):
        """Update profile fields owned by Django."""
        profile, _created = FoundationUserProfile.objects.get_or_create(user=user)
        allowed_fields = {"avatar_url", "phone", "language", "timezone", "two_factor_enabled"}
        for field_name, value in profile_fields.items():
            if field_name in allowed_fields:
                setattr(profile, field_name, value)
        profile.save()
        return profile


class FoundationAuthService:
    """Own authentication token lifecycle in Django."""

    def __init__(self, permission_service=None):
        """Allow tests to pass a permission service double."""
        self.permission_service = permission_service or FoundationPermissionService()

    @staticmethod
    def hash_token(raw_token):
        """Hash a raw token before storing or lookup."""
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    def login(self, email, password, remote_addr="", user_agent=""):
        """Verify credentials and create a Django-owned auth token."""
        try:
            user = FoundationUser.objects.select_related("role").get(email=email, is_active=True)
        except FoundationUser.DoesNotExist as exc:
            raise PermissionDenied("Invalid credentials.") from exc

        if not check_password(password, user.password_hash):
            raise PermissionDenied("Invalid credentials.")

        raw_token = secrets.token_urlsafe(32)
        token = FoundationAuthToken.objects.create(
            user=user,
            token_hash=self.hash_token(raw_token),
            expires_at=timezone.now() + timedelta(hours=TOKEN_TTL_HOURS),
            remote_addr=remote_addr or "",
            user_agent=user_agent or "",
        )
        return raw_token, token

    def authenticate_token(self, raw_token):
        """Return the active user for a raw token."""
        if not raw_token:
            raise PermissionDenied("Authentication token is required.")
        token_hash = self.hash_token(raw_token)
        try:
            token = FoundationAuthToken.objects.select_related("user", "user__role").get(
                token_hash=token_hash,
                revoked_at__isnull=True,
                expires_at__gte=timezone.now(),
            )
        except FoundationAuthToken.DoesNotExist as exc:
            raise PermissionDenied("Invalid or expired token.") from exc
        return token.user

    def logout(self, raw_token):
        """Revoke a Django-owned auth token."""
        token_hash = self.hash_token(raw_token)
        updated = FoundationAuthToken.objects.filter(
            token_hash=token_hash,
            revoked_at__isnull=True,
        ).update(revoked_at=timezone.now())
        return updated > 0

    def user_from_authorization_header(self, authorization):
        """Parse a Bearer token from an Authorization header."""
        prefix = "Bearer "
        if not authorization or not authorization.startswith(prefix):
            raise PermissionDenied("Bearer token is required.")
        return self.authenticate_token(authorization[len(prefix) :].strip())
