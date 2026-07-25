"""Read-only authentication compatibility helpers."""

from dataclasses import dataclass

from apps.accounts.repositories.auth_repository import AdminUserRepository


ROLE_PERMISSIONS = {
    "admin": {"*": {"read", "write"}},
    "editor": {
        "dashboard": {"read", "write"},
        "products": {"read", "write"},
        "categories": {"read", "write"},
        "news": {"read", "write"},
        "media": {"read", "write"},
        "pages": {"read", "write"},
        "menus": {"read", "write"},
        "banners": {"read", "write"},
        "contacts": {"read", "write"},
        "quotes": {"read", "write"},
        "customers": {"read", "write"},
        "newsletter": {"read", "write"},
        "ai": {"read", "write"},
        "developer": {"read", "write"},
    },
    "viewer": {"*": {"read"}},
}


@dataclass(frozen=True)
class PasswordHashInfo:
    """Safe password hash metadata without exposing the hash value."""

    algorithm: str
    needs_upgrade: bool
    is_supported: bool


class PasswordHashInspector:
    """Classify legacy password hashes without verifying real passwords."""

    @staticmethod
    def inspect(password_hash):
        """Return safe metadata for a password hash."""
        if str(password_hash or "").startswith("pbkdf2_sha256$"):
            return PasswordHashInfo(
                algorithm="pbkdf2_sha256",
                needs_upgrade=False,
                is_supported=True,
            )

        return PasswordHashInfo(
            algorithm="legacy_sha256",
            needs_upgrade=True,
            is_supported=True,
        )


class PermissionMatrix:
    """Map legacy admin/editor/viewer roles to permission decisions."""

    def has_permission(self, role, module_name, action="read"):
        """Return whether a role can perform an action on a module."""
        role_permissions = ROLE_PERMISSIONS.get(role)
        if not role_permissions:
            return False

        if "*" in role_permissions:
            return action in role_permissions["*"]

        return action in role_permissions.get(module_name, set())


class AuthCompatibilityService:
    """Read-only service for auth migration compatibility checks."""

    def __init__(self, admin_user_repository=None, permission_matrix=None):
        """Allow tests to pass repository doubles."""
        self.admin_user_repository = admin_user_repository or AdminUserRepository()
        self.permission_matrix = permission_matrix or PermissionMatrix()
        self.password_hash_inspector = PasswordHashInspector()

    def get_user_auth_profile(self, admin_id):
        """Return safe auth profile data without password hash."""
        user = self.admin_user_repository.get_user(admin_id)
        return {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "two_factor_enabled": user.two_factor_enabled,
        }

    def inspect_user_password_hash(self, email):
        """Inspect hash compatibility without returning the hash value."""
        user = self.admin_user_repository.get_user_for_credential_check(email)
        return self.password_hash_inspector.inspect(user.password_hash)

    def can_attempt_login(self, admin_user):
        """Read-only login boundary check used before any future auth migration."""
        return bool(admin_user and admin_user.is_active)

    def is_session_expired(self, session, now_timestamp):
        """Return whether a legacy session is expired without updating last_seen_at."""
        return int(session.expires_at) < int(now_timestamp)

    def is_password_reset_token_usable(self, reset_token, now_timestamp):
        """Return whether a reset token is unused and not expired."""
        return reset_token.used_at is None and int(reset_token.expires_at) >= int(now_timestamp)

    def can_use_two_factor_challenge(self, challenge):
        """Return whether a 2FA challenge has not been used."""
        return challenge.used_at in {None, ""}

    def has_permission(self, role, module_name, action="read"):
        """Delegate permission decision to the legacy-compatible matrix."""
        return self.permission_matrix.has_permission(role, module_name, action)
