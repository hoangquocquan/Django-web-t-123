"""Central URL map for read-only migrated business APIs."""

from django.urls import path

from .views.auth import permissions, profile
from .views.catalog import categories, materials, product_detail, products
from .views.cms import menu, page_detail, pages
from .views.crm import contact_requests, customer_detail, customers
from .views.sales import quote_detail, quote_files, quotes


urlpatterns = [
    path("catalog/products/", products, name="api-catalog-products"),
    path("catalog/products/<int:product_id>/", product_detail, name="api-catalog-product-detail"),
    path("catalog/categories/", categories, name="api-catalog-categories"),
    path("catalog/materials/", materials, name="api-catalog-materials"),
    path("crm/customers/", customers, name="api-crm-customers"),
    path("crm/customers/<int:customer_id>/", customer_detail, name="api-crm-customer-detail"),
    path("crm/contact-requests/", contact_requests, name="api-crm-contact-requests"),
    path("sales/quotes/", quotes, name="api-sales-quotes"),
    path("sales/quotes/<int:quote_id>/", quote_detail, name="api-sales-quote-detail"),
    path("sales/quotes/<int:quote_id>/files/", quote_files, name="api-sales-quote-files"),
    path("cms/pages/", pages, name="api-cms-pages"),
    path("cms/pages/<slug:slug>/", page_detail, name="api-cms-page-detail"),
    path("cms/menu/", menu, name="api-cms-menu"),
    path("auth/profile/", profile, name="api-auth-profile"),
    path("auth/permissions/", permissions, name="api-auth-permissions"),
]
