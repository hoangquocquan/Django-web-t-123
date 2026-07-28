"""Serializers for Django-owned foundation APIs."""

from rest_framework import serializers


class FoundationLoginSerializer(serializers.Serializer):
    """Validate a login request before the service checks credentials."""

    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)


class FoundationUserCreateSerializer(serializers.Serializer):
    """Validate user creation fields owned by Django."""

    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=160)
    password = serializers.CharField(trim_whitespace=False)
    role = serializers.CharField(default="viewer", max_length=50)
    avatar_url = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=50)
    language = serializers.CharField(required=False, allow_blank=True, max_length=10)
    timezone = serializers.CharField(required=False, allow_blank=True, max_length=80)
    two_factor_enabled = serializers.BooleanField(required=False)


class FoundationProfileUpdateSerializer(serializers.Serializer):
    """Validate profile fields that can be edited by the foundation API."""

    avatar_url = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=50)
    language = serializers.CharField(required=False, allow_blank=True, max_length=10)
    timezone = serializers.CharField(required=False, allow_blank=True, max_length=80)
    two_factor_enabled = serializers.BooleanField(required=False)


class FoundationPermissionCheckSerializer(serializers.Serializer):
    """Validate one permission check request."""

    module = serializers.CharField(max_length=80)
    action = serializers.CharField(default="read", max_length=40)


def profile_to_dict(profile):
    """Convert a Django-owned profile to API JSON."""
    return {
        "avatar_url": profile.avatar_url,
        "phone": profile.phone,
        "language": profile.language,
        "timezone": profile.timezone,
        "two_factor_enabled": profile.two_factor_enabled,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


def user_to_dict(user):
    """Convert a Django-owned user to API JSON without exposing password data."""
    profile = getattr(user, "profile", None)
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.name,
        "is_active": user.is_active,
        "legacy_admin_id": user.legacy_admin_id,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "profile": profile_to_dict(profile) if profile else None,
    }


def role_to_dict(role, permission_service):
    """Convert a role and its permissions to API JSON."""
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "permissions": permission_service.permissions_for_role(role),
        "created_at": role.created_at.isoformat() if role.created_at else None,
    }
