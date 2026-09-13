"""Fail-closed authentication and exact Phase 3 permission checks for Phase 4A."""

from rest_framework import exceptions
from rest_framework.permissions import BasePermission


CANONICAL_ROLE_MATRIX = {
    "customer:view": frozenset({"Admin", "Sales", "Manager"}),
    "part:view": frozenset({"Admin", "Sales", "Manager"}),
    "material:view": frozenset({"Admin", "Sales", "Manager"}),
    "rfq:view": frozenset({"Admin", "Sales", "Manager"}),
    "quotation:view": frozenset({"Admin", "Sales", "Manager"}),
    "order:view": frozenset({"Admin", "Sales", "Manager"}),
    "audit:view": frozenset({"Admin", "Manager"}),
}


ENTITY_PERMISSION_CODES = {
    "customer": "customer:view",
    "part": "part:view",
    "material": "material:view",
    "rfq": "rfq:view",
    "quotation": "quotation:view",
    "order": "order:view",
}


class CanonicalReadPermission(BasePermission):
    """Require an active user, canonical role, and exact non-wildcard grant."""

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            raise exceptions.NotAuthenticated()
        if not getattr(user, "is_active", False):
            raise exceptions.AuthenticationFailed("Inactive user.")

        role = getattr(user, "role", None)
        role_name = getattr(role, "name", None)
        permission_code = view.get_permission_code()
        allowed_roles = CANONICAL_ROLE_MATRIX.get(permission_code, frozenset())
        if role_name not in allowed_roles:
            raise exceptions.PermissionDenied("Canonical role is not authorized.")

        module, action = permission_code.split(":", 1)
        has_exact_grant = role.permissions.filter(
            code=permission_code,
            module=module,
            action=action,
        ).exists()
        if not has_exact_grant:
            raise exceptions.PermissionDenied("Exact canonical permission is required.")
        return True
