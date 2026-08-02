"""Infrastructure and compatibility views for the Django migration backend."""

import secrets

from django.conf import settings
from django.http import HttpResponse
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.common.observability import MetricsRegistry, OperationalHealthService

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


def _operations_authorized(request):
    expected = str(getattr(settings, "METRICS_BEARER_TOKEN", "") or "")
    authorization = request.META.get("HTTP_AUTHORIZATION", "")
    supplied = authorization[7:] if authorization.startswith("Bearer ") else ""
    return bool(expected and supplied and secrets.compare_digest(expected, supplied))


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def prometheus_metrics(request):
    """Export sanitized Prometheus text for an authenticated local scraper."""
    if not _operations_authorized(request):
        return Response(
            {"success": False, "error": {"code": "metrics_unauthorized"}},
            status=401,
        )
    lines = MetricsRegistry().render()
    lines.extend(OperationalHealthService().prometheus_lines())
    return HttpResponse(
        "\n".join(lines) + "\n", content_type="text/plain; version=0.0.4"
    )


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def operations_health(request):
    """Return a protected dependency snapshot for uptime checks."""
    if not _operations_authorized(request):
        return Response(
            {"success": False, "error": {"code": "operations_unauthorized"}},
            status=401,
        )
    return Response({"success": True, "data": OperationalHealthService().snapshot()})
