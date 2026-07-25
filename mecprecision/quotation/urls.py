"""URL của module Quotation.

Nhóm URL này được gắn dưới `/quotation/` từ file `core/urls.py`.
"""

from django.urls import path

from . import views

app_name = "quotation"

urlpatterns = [
    path("", views.quote_list, name="list"),
    path("<int:quote_id>/", views.quote_detail, name="detail"),
    path("api/", views.quote_list_api, name="api-list"),
    path("api/create/", views.public_quote_create_api, name="api-create"),
    path("api/<int:quote_id>/", views.quote_detail_api, name="api-detail"),
]
