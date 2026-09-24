"""Central DRF authentication adapter for Django foundation tokens."""

from django.core.exceptions import PermissionDenied
from rest_framework import authentication, exceptions

from apps.foundation.services import FoundationAuthService


class FoundationBearerAuthentication(authentication.BaseAuthentication):
    """Resolve optional Bearer credentials through the foundation auth service."""

    keyword = "Bearer"

    def authenticate(self, request):
        """Return None when absent and fail closed when credentials are invalid."""
        authorization = authentication.get_authorization_header(request).decode("utf-8")
        if not authorization:
            return None
        try:
            user = FoundationAuthService().user_from_authorization_header(authorization)
        except PermissionDenied as exc:
            raise exceptions.AuthenticationFailed(str(exc)) from exc
        return user, authorization.removeprefix(f"{self.keyword} ").strip()

    def authenticate_header(self, request):
        """Advertise the expected authentication scheme."""
        return self.keyword
