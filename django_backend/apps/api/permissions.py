"""Permission helpers for Phase 9.1 read-only business APIs."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class ReadOnlyApiPermission(BasePermission):
    """Allow only safe HTTP methods during business API cutover.

    Phase 9.1 prepares read-only APIs. Write methods are blocked at the
    permission layer even if a future view accidentally accepts them.
    """

    message = "Phase 9.1 business APIs are read-only."

    def has_permission(self, request, view):
        """Return True only for GET/HEAD/OPTIONS requests."""
        return request.method in SAFE_METHODS


class FoundationModulePermission(BasePermission):
    """Central module permission class for DRF class-based views."""

    message = "The authenticated user lacks the required module permission."

    def has_permission(self, request, view):
        """Map safe methods to read and mutation methods to write by default."""
        from apps.foundation.services import FoundationPermissionService

        module = getattr(view, "permission_module", "")
        action = getattr(
            view,
            "permission_action",
            "read" if request.method in SAFE_METHODS else "write",
        )
        return bool(module) and FoundationPermissionService().has_permission(
            getattr(request, "user", None),
            module,
            action,
        )
