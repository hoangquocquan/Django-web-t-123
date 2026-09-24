"""Serializer helpers for authentication preparation APIs."""


def profile_to_dict(profile):
    """Return only safe profile fields, never password hashes or tokens."""
    return {
        "id": profile["id"],
        "full_name": profile["full_name"],
        "email": profile["email"],
        "role": profile["role"],
        "is_active": profile["is_active"],
        "two_factor_enabled": profile["two_factor_enabled"],
    }
