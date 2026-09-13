"""Stable response, error, filtering, ordering, and pagination contract for Phase 4A."""

from __future__ import annotations

from dataclasses import dataclass

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import APIView


DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
PAGINATION_PARAMETERS = frozenset({"limit", "offset", "ordering"})


class CanonicalApiError(Exception):
    """An expected API failure with a stable machine-readable code."""

    def __init__(self, code, message, *, status_code=status.HTTP_400_BAD_REQUEST, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def success(data):
    """Return the canonical success envelope."""
    return Response({"success": True, "data": data})


def error(code, message, *, status_code, details=None):
    """Return the canonical error envelope without leaking exception internals."""
    payload = {"success": False, "error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return Response(payload, status=status_code)


def _integer(value, *, name, minimum, maximum=None):
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise CanonicalApiError(
            "invalid_query_parameter",
            f"`{name}` must be an integer.",
        ) from exc
    if parsed < minimum or (maximum is not None and parsed > maximum):
        maximum_text = f" and at most {maximum}" if maximum is not None else ""
        raise CanonicalApiError(
            "invalid_query_parameter",
            f"`{name}` must be at least {minimum}{maximum_text}.",
        )
    return parsed


def integer_filter(value):
    """Parse one positive integer filter value."""
    return _integer(value, name="filter", minimum=1)


def boolean_filter(value):
    """Parse a strict boolean filter value."""
    normalized = str(value).lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise CanonicalApiError(
        "invalid_query_parameter",
        "Boolean filters must be `true` or `false`.",
    )


def string_filter(value):
    """Keep an explicitly allowlisted string filter exact."""
    return str(value)


@dataclass(frozen=True)
class FilterSpec:
    """Map one public filter name to one controlled ORM lookup."""

    lookup: str
    converter: object = string_filter


def paginated_data(
    request,
    queryset,
    serializer,
    *,
    filters=None,
    ordering=None,
    default_ordering=("id",),
):
    """Apply only allowlisted query operations and return bounded page data."""
    filters = filters or {}
    ordering = ordering or {}
    received = set(request.query_params)
    unsupported = sorted(received - PAGINATION_PARAMETERS - set(filters))
    if unsupported:
        raise CanonicalApiError(
            "unsupported_filter",
            "Unsupported query parameter.",
            details={"parameters": unsupported},
        )

    filter_values = {}
    for public_name, spec in filters.items():
        if public_name in request.query_params:
            raw_value = request.query_params.get(public_name)
            try:
                filter_values[spec.lookup] = spec.converter(raw_value)
            except CanonicalApiError as exc:
                exc.message = f"Invalid `{public_name}` filter."
                raise
    if filter_values:
        queryset = queryset.filter(**filter_values)

    requested_ordering = request.query_params.get("ordering", "")
    if requested_ordering:
        descending = requested_ordering.startswith("-")
        public_name = requested_ordering[1:] if descending else requested_ordering
        if public_name not in ordering:
            raise CanonicalApiError(
                "unsupported_ordering",
                "Unsupported ordering field.",
                details={"field": requested_ordering},
            )
        orm_name = ordering[public_name]
        queryset = queryset.order_by(f"-{orm_name}" if descending else orm_name)
    else:
        queryset = queryset.order_by(*default_ordering)

    raw_limit = request.query_params.get("limit", DEFAULT_PAGE_SIZE)
    raw_offset = request.query_params.get("offset", 0)
    limit = _integer(raw_limit, name="limit", minimum=1, maximum=MAX_PAGE_SIZE)
    offset = _integer(raw_offset, name="offset", minimum=0)
    count = queryset.count()
    objects = list(queryset[offset : offset + limit])
    next_offset = offset + limit if offset + limit < count else None
    previous_offset = max(0, offset - limit) if offset > 0 else None
    return {
        "count": count,
        "limit": limit,
        "offset": offset,
        "next_offset": next_offset,
        "previous_offset": previous_offset,
        "results": [serializer(item) for item in objects],
    }


class CanonicalAPIView(APIView):
    """Base view that preserves one safe error envelope for Phase 4A only."""

    http_method_names = ["get", "head", "options"]
    resource_name = "Resource"

    def handle_exception(self, exc):
        if isinstance(exc, CanonicalApiError):
            return error(
                exc.code,
                exc.message,
                status_code=exc.status_code,
                details=exc.details,
            )
        if isinstance(exc, exceptions.NotAuthenticated):
            return error(
                "authentication_required",
                "Authentication credentials are required.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        if isinstance(exc, exceptions.AuthenticationFailed):
            return error(
                "authentication_failed",
                "Authentication credentials are invalid or inactive.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        if isinstance(exc, exceptions.PermissionDenied):
            return error(
                "permission_denied",
                "The authenticated user is not authorized for this resource.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        if isinstance(exc, (exceptions.NotFound, ObjectDoesNotExist)):
            return error(
                "not_found",
                f"{self.resource_name} was not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if isinstance(exc, exceptions.MethodNotAllowed):
            return error(
                "method_not_allowed",
                "Only GET, HEAD, and OPTIONS are allowed.",
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        if isinstance(exc, exceptions.ValidationError):
            return error(
                "validation_error",
                "Request validation failed.",
                status_code=status.HTTP_400_BAD_REQUEST,
                details=exc.detail,
            )
        return super().handle_exception(exc)
