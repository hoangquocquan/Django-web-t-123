"""Small response helpers shared by read-only API views."""

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.response import Response


def ok(data):
    """Return the standard success envelope for Phase 9.1 APIs."""
    return Response({"success": True, "data": data})


def list_ok(items):
    """Return a list response with a count for frontend pagination readiness."""
    materialized_items = list(items)
    return ok(
        {
            "count": len(materialized_items),
            "results": materialized_items,
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
