"""URL của module Customers.

Nhóm URL này được gắn dưới `/customers/` từ file `core/urls.py`.
"""

from django.urls import path

from . import views

app_name = "customers"

urlpatterns = [
    path("", views.customer_list, name="list"),
    path("<int:customer_id>/", views.customer_detail, name="detail"),
    path("contacts/", views.contact_request_list, name="contact-list"),
    path("contacts/<int:contact_id>/", views.contact_request_detail, name="contact-detail"),
    path("api/", views.customer_list_api, name="api-list"),
    path("api/<int:customer_id>/", views.customer_detail_api, name="api-detail"),
    path("api/contacts/", views.contact_request_list_api, name="api-contact-list"),
    path("api/contacts/<int:contact_id>/", views.contact_request_detail_api, name="api-contact-detail"),
]
