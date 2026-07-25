"""URL của module Common/System."""

from django.urls import path

from . import views

app_name = "common"

urlpatterns = [
    path("", views.common_home, name="home"),
    path("api/health/", views.health_api, name="api-health"),
    path("api/pages/", views.pages_api, name="api-pages"),
    path("api/menu/", views.menu_api, name="api-menu"),
]
