"""Root URL routing for the parallel Django backend."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("apps.website.urls")),
    path("admin/", include("apps.admin_ui.urls")),
    path("business/", include("apps.business_ui.urls")),
    path("django-admin/", admin.site.urls),
    path("api/", include("apps.core.urls")),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/", include("apps.api.urls")),
]
