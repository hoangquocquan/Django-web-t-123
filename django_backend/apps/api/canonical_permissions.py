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

CANONICAL_COMMAND_ROLE_MATRIX = {
    "customer:create": frozenset({"Admin", "Sales"}),
    "customer:change": frozenset({"Admin", "Sales"}),
    "customer:archive": frozenset({"Admin", "Sales"}),
    "part:manage": frozenset({"Admin"}),
    "part:archive": frozenset({"Admin"}),
    "material:manage": frozenset({"Admin"}),
    "material:archive": frozenset({"Admin"}),
    "rfq:create": frozenset({"Admin", "Sales"}),
    "rfq:change": frozenset({"Admin", "Sales"}),
    "rfq:archive": frozenset({"Admin", "Sales"}),
    "rfq:submit": frozenset({"Admin", "Sales"}),
    "rfq:review": frozenset({"Manager"}),
    "rfq:document_upload": frozenset({"Admin", "Sales"}),
    "rfq:document_download": frozenset({"Admin", "Sales", "Manager"}),
    "quotation:create_revision": frozenset({"Admin", "Sales"}),
    "quotation:change": frozenset({"Admin", "Sales"}),
    "quotation:archive": frozenset({"Admin", "Sales"}),
    "quotation:submit": frozenset({"Admin", "Sales"}),
    "quotation:approve": frozenset({"Manager"}),
    "quotation:reject": frozenset({"Manager"}),
    "quotation:send": frozenset({"Admin", "Sales"}),
    "quotation:record_customer_decision": frozenset({"Admin", "Sales"}),
    "quotation:convert": frozenset({"Admin", "Sales"}),
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
        if not getattr(role, "is_active", False):
            raise exceptions.PermissionDenied("Inactive canonical role.")
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


def has_exact_permission(user, permission_code):
    """Check one exact code/module/action tuple without wildcard fallback."""
    role = getattr(user, "role", None)
    if role is None or not getattr(role, "is_active", False):
        return False
    module, action = permission_code.split(":", 1)
    return role.permissions.filter(
        code=permission_code,
        module=module,
        action=action,
    ).exists()


class CanonicalCommandPermission(BasePermission):
    """Require exact visibility and command grants for a Phase 4B endpoint."""

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            raise exceptions.NotAuthenticated()
        if not getattr(user, "is_active", False):
            raise exceptions.AuthenticationFailed("Inactive user.")

        permission_code = view.get_permission_code()
        role_name = getattr(getattr(user, "role", None), "name", None)
        if not getattr(getattr(user, "role", None), "is_active", False):
            raise exceptions.PermissionDenied("Inactive canonical role.")
        if role_name not in CANONICAL_COMMAND_ROLE_MATRIX.get(
            permission_code, frozenset()
        ):
            raise exceptions.PermissionDenied("Canonical role is not authorized.")
        if not has_exact_permission(user, permission_code):
            raise exceptions.PermissionDenied("Exact command permission is required.")

        visibility_code = view.get_visibility_permission_code()
        if not has_exact_permission(user, visibility_code):
            raise exceptions.PermissionDenied("Exact view permission is required.")
        return True
