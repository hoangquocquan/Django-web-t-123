"""Authentication preparation API views for Phase 9.1."""

from rest_framework.decorators import api_view, permission_classes

from apps.accounts.services.auth_compatibility_service import AuthCompatibilityService
from apps.api.permissions import ReadOnlyApiPermission
from apps.api.serializers.auth import profile_to_dict
from apps.api.views.helpers import handle_not_found, ok


def _admin_id_from_request(request):
    """Read demo admin ID without creating sessions or tokens."""
    return request.headers.get("X-Demo-Admin-Id") or request.query_params.get("admin_id", "1")


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def profile(request):
    """Return safe profile fields only; login/session cutover is not implemented."""
    service = AuthCompatibilityService()
    admin_id = _admin_id_from_request(request)
    return handle_not_found(
        "Admin profile",
        lambda: ok(profile_to_dict(service.get_user_auth_profile(admin_id))),
    )


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def permissions(request):
    """Return safe role permissions without mutating auth state."""
    role = request.query_params.get("role", "viewer")
    service = AuthCompatibilityService()
    return ok(
        {
            "role": role,
            "permissions": service.get_permissions_for_role(role),
            "login_cutover": False,
            "session_mutation": False,
        }
    )
