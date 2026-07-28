"""Django-owned foundation API views for auth, users, and permissions."""

from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.api.serializers.foundation import (
    FoundationLoginSerializer,
    FoundationPermissionCheckSerializer,
    FoundationProfileUpdateSerializer,
    FoundationUserCreateSerializer,
    role_to_dict,
    user_to_dict,
)
from apps.api.views.helpers import handle_not_found, ok, paginated_ok
from apps.foundation.models import FoundationRole
from apps.foundation.services import (
    FoundationAuthService,
    FoundationPermissionService,
    FoundationUserService,
)


def _request_context(request):
    """Collect non-secret request metadata for token audit rows."""
    return {
        "remote_addr": request.META.get("REMOTE_ADDR", ""),
        "user_agent": request.META.get("HTTP_USER_AGENT", ""),
    }


def _authorization_header(request):
    """Read the Authorization header in a test-client friendly way."""
    return request.META.get("HTTP_AUTHORIZATION", "")


def _authenticated_user(request):
    """Resolve the current Django-owned user from a Bearer token."""
    return FoundationAuthService().user_from_authorization_header(_authorization_header(request))


def _require_foundation_permission(request, module, action="read"):
    """Authenticate a request and enforce a Django-owned permission."""
    user = _authenticated_user(request)
    FoundationPermissionService().require_permission(user, module, action)
    return user


def _permission_error_response(exc):
    """Return a consistent JSON response for auth and permission failures."""
    return Response(
        {
            "success": False,
            "error": {
                "code": "permission_denied",
                "message": str(exc),
            },
        },
        status=status.HTTP_403_FORBIDDEN,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def foundation_login(request):
    """Create a Django-owned auth token from email and password."""
    serializer = FoundationLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    service = FoundationAuthService()
    try:
        raw_token, token = service.login(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            **_request_context(request),
        )
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    return ok(
        {
            "token": raw_token,
            "expires_at": token.expires_at.isoformat(),
            "user": user_to_dict(token.user),
        }
    )


@api_view(["POST"])
def foundation_logout(request):
    """Revoke the current Django-owned auth token."""
    try:
        user = _authenticated_user(request)
        FoundationPermissionService().require_permission(user, "auth", "read")
        authorization = _authorization_header(request)
        FoundationAuthService().logout(authorization.replace("Bearer ", "", 1).strip())
    except PermissionDenied as exc:
        return _permission_error_response(exc)
    return ok({"logged_out": True})


@api_view(["GET", "POST"])
def foundation_users(request):
    """List or create Django-owned foundation users."""
    try:
        action = "write" if request.method == "POST" else "read"
        _require_foundation_permission(request, "users", action)
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    service = FoundationUserService()
    if request.method == "GET":
        return paginated_ok(request, service.list_users(), user_to_dict)

    serializer = FoundationUserCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    profile = {
        key: serializer.validated_data[key]
        for key in ["avatar_url", "phone", "language", "timezone", "two_factor_enabled"]
        if key in serializer.validated_data
    }
    try:
        user = service.create_user(
            email=serializer.validated_data["email"],
            full_name=serializer.validated_data["full_name"],
            password=serializer.validated_data["password"],
            role_name=serializer.validated_data.get("role", "viewer"),
            profile=profile,
        )
    except ValidationError as exc:
        return Response(
            {
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": "; ".join(str(message) for message in exc.messages),
                },
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({"success": True, "data": user_to_dict(user)}, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT"])
def foundation_user_profile(request, user_id):
    """Read or update a Django-owned user profile."""
    try:
        action = "write" if request.method == "PUT" else "read"
        _require_foundation_permission(request, "users", action)
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    service = FoundationUserService()

    def execute():
        user = service.get_user(user_id)
        if request.method == "GET":
            return ok(user_to_dict(user))

        serializer = FoundationProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service.update_profile(user, **serializer.validated_data)
        return ok(user_to_dict(service.get_user(user_id)))

    return handle_not_found("Foundation user", execute)


@api_view(["GET"])
def foundation_roles(request):
    """List Django-owned roles and their permission matrix."""
    try:
        _require_foundation_permission(request, "permissions", "read")
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    permission_service = FoundationPermissionService()
    roles = FoundationRole.objects.prefetch_related("permissions").all()
    return ok([role_to_dict(role, permission_service) for role in roles])


@api_view(["POST"])
def foundation_permission_check(request):
    """Check whether the current user has one Django-owned permission."""
    try:
        user = _authenticated_user(request)
    except PermissionDenied as exc:
        return _permission_error_response(exc)

    serializer = FoundationPermissionCheckSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    permission_service = FoundationPermissionService()
    module = serializer.validated_data["module"]
    action = serializer.validated_data.get("action", "read")
    return ok(
        {
            "module": module,
            "action": action,
            "allowed": permission_service.has_permission(user, module, action),
            "user": user_to_dict(user),
        }
    )
