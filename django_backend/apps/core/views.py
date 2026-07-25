"""Infrastructure-only health check views for migration Phase 2."""

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def root_health(request):
    """Return a minimal response proving the Django backend is running."""
    return Response(
        {
            "success": True,
            "message": "Django foundation ready",
            "phase": 2,
        }
    )


@api_view(["GET"])
def health_check(request):
    """Return the Phase 2 health check response."""
    return Response(
        {
            "success": True,
            "message": "Django foundation ready",
            "phase": 2,
        }
    )
