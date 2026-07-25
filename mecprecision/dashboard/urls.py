"""URL của module Dashboard."""

from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_home, name="home"),
    path("api/", views.dashboard_api, name="api"),
    path("api/track-visit/", views.track_visit_api, name="api-track-visit"),
]
