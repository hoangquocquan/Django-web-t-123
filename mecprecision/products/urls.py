"""URL cho app products trong Django."""

from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    path("", views.product_list, name="list"),
    path("<int:product_id>/", views.product_detail, name="detail"),
    path("api/", views.product_list_api, name="api-list"),
    path("api/<int:product_id>/", views.product_detail_api, name="api-detail"),
]
