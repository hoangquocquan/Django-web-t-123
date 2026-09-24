"""URL routing for the core app."""

from django.urls import path, re_path

from .views import (
    api_cutover_status,
    health_check,
    health_rollback_status,
    operations_health,
    phase6_liveness,
    phase6_readiness,
    prometheus_metrics,
)

urlpatterns = [
    path("phase6/live/", phase6_liveness, name="phase6-liveness"),
    path("phase6/ready/", phase6_readiness, name="phase6-readiness"),
    re_path(r"^health/?$", health_check, name="health"),
    re_path(r"^cutover/health/?$", api_cutover_status, name="health-cutover-status"),
    re_path(
        r"^cutover/health/rollback/?$",
        health_rollback_status,
        name="health-rollback-status",
    ),
    path("cutover/", api_cutover_status, name="api-cutover-status"),
    path("metrics/", prometheus_metrics, name="prometheus-metrics"),
    path("operations/health/", operations_health, name="operations-health"),
]
