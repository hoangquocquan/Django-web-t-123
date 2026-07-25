"""Root URL routing for the parallel Django backend."""

from django.contrib import admin
from django.urls import include, path

from apps.core.views import root_health


urlpatterns = [
    path("", root_health, name="root-health"),
    path("admin/", admin.site.urls),
    path("api/", include("apps.core.urls")),
    path("api/v1/", include("apps.core.urls")),
]
