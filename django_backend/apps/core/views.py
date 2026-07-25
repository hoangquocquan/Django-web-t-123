"""Infrastructure and compatibility views for the Django migration backend."""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .api_compatibility import (
    build_cutover_status_response,
    build_health_rollback_response,
    build_legacy_health_response,
)


@api_view(["GET"])
def root_health(request):
    """Return a minimal response proving the Django backend is running."""
    return Response(
        {
            "success": True,
            "message": "Django migration backend ready",
            "phase": 9,
        }
    )


@api_view(["GET"])
def health_check(request):
    """Serve the legacy-compatible health API from Django."""
    return Response(build_legacy_health_response())


@api_view(["GET"])
def api_cutover_status(request):
    """Show the selected Phase 9 cutover route and compatibility contract."""
    return Response(build_cutover_status_response())


@api_view(["GET"])
def health_rollback_status(request):
    """Expose the rollback plan for the health endpoint cutover."""
    return Response(build_health_rollback_response())
