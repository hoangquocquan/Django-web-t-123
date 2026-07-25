"""URL routing for the core app."""

from django.urls import path, re_path

from .views import api_cutover_status, health_check, health_rollback_status


urlpatterns = [
    re_path(r"^health/?$", health_check, name="health"),
    re_path(r"^cutover/health/?$", api_cutover_status, name="health-cutover-status"),
    re_path(
        r"^cutover/health/rollback/?$",
        health_rollback_status,
        name="health-rollback-status",
    ),
    path("cutover/", api_cutover_status, name="api-cutover-status"),
]
