"""Small response helpers shared by read-only API views."""

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.response import Response

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def ok(data):
    """Return the standard success envelope for business APIs."""
    return Response({"success": True, "data": data})


def created(data):
    """Return the standard success envelope for newly accepted resources."""
    return Response({"success": True, "data": data}, status=status.HTTP_201_CREATED)


def bad_request(code, message):
    """Return a consistent 400 response for invalid API input."""
    return Response(
        {
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def _positive_int(value, default):
    """Parse a non-negative integer query parameter."""
    if value in {None, ""}:
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    if parsed < 0:
        return None
    return parsed


def pagination_from_request(request):
    """Read and clamp pagination parameters for list APIs."""
    limit = _positive_int(request.query_params.get("limit"), DEFAULT_LIMIT)
    offset = _positive_int(request.query_params.get("offset"), 0)

    if limit is None or offset is None:
        return None, bad_request(
            "invalid_pagination",
            "`limit` and `offset` must be non-negative integers.",
        )

    return {
        "limit": min(limit, MAX_LIMIT),
        "offset": offset,
    }, None


def list_ok(items):
    """Return a non-paginated list response for compatibility helpers."""
    materialized_items = list(items)
    return ok(
        {
            "count": len(materialized_items),
            "limit": len(materialized_items),
            "offset": 0,
            "next_offset": None,
            "results": materialized_items,
        }
    )


def paginated_ok(request, queryset, serializer):
    """Return a paginated list response without loading unnecessary rows."""
    pagination, error_response = pagination_from_request(request)
    if error_response:
        return error_response

    limit = pagination["limit"]
    offset = pagination["offset"]
    total_count = queryset.count()
    page_items = queryset[offset : offset + limit]
    next_offset = offset + limit if offset + limit < total_count else None

    return ok(
        {
            "count": total_count,
            "limit": limit,
            "offset": offset,
            "next_offset": next_offset,
            "results": [serializer(item) for item in page_items],
        }
    )


def not_found(resource_name):
    """Return a consistent 404 response without exposing internals."""
    return Response(
        {
            "success": False,
            "error": {
                "code": "not_found",
                "message": f"{resource_name} was not found.",
            },
        },
        status=status.HTTP_404_NOT_FOUND,
    )


def handle_not_found(resource_name, callback):
    """Run a callback and convert Django DoesNotExist into API 404 JSON."""
    try:
        return callback()
    except ObjectDoesNotExist:
        return not_found(resource_name)
