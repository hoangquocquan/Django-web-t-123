"""Health check views for migration step 1."""

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def root_health(request):
    """Return a minimal response proving the Django backend is running."""
    return Response(
        {
            "status": "django running",
            "version": "step-1",
        }
    )


@api_view(["GET"])
def health_check(request):
    """Return the step 1 migration health check response."""
    return Response(
        {
            "success": True,
            "message": "Django migration step 1 completed",
        }
    )
