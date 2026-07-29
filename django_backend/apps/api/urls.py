"""Central URL map for migrated business APIs and legacy replacements."""

from django.urls import path

from .views.auth import permissions, profile
from .views.business_core import (
    business_customer_detail,
    business_customers,
    business_product_detail,
    business_products,
    inventory_adjust,
    inventory_items,
    inventory_warehouses,
)
from .views.catalog import categories, materials, product_detail, products
from .views.cms import menu, page_detail, pages
from .views.crm import contact_requests, customer_detail, customers
from .views.foundation import (
    foundation_login,
    foundation_logout,
    foundation_permission_check,
    foundation_roles,
    foundation_user_profile,
    foundation_users,
)
from .views.newsletter import subscribers as newsletter_subscribers
from .views.replacement import (
    ai_chat,
    aws_demo,
    capabilities,
    external_weather,
    home,
    news,
    openapi_schema,
    version,
)
from .views.sales import quote_detail, quote_files, quotes
from .views.transaction_domain import (
    order_detail as transaction_order_detail,
    orders as transaction_orders,
    transactions,
    workflows,
)


urlpatterns = [
    path("catalog/products/", products, name="api-catalog-products"),
    path("catalog/products/<int:product_id>/", product_detail, name="api-catalog-product-detail"),
    path("catalog/categories/", categories, name="api-catalog-categories"),
    path("catalog/materials/", materials, name="api-catalog-materials"),
    path("catalog/capabilities/", capabilities, name="api-catalog-capabilities"),
    path("business/products/", business_products, name="api-business-products"),
    path(
        "business/products/<int:product_id>/",
        business_product_detail,
        name="api-business-product-detail",
    ),
    path("crm/customers/", customers, name="api-crm-customers"),
    path("crm/customers/<int:customer_id>/", customer_detail, name="api-crm-customer-detail"),
    path("crm/contact-requests/", contact_requests, name="api-crm-contact-requests"),
    path("business/customers/", business_customers, name="api-business-customers"),
    path(
        "business/customers/<int:customer_id>/",
        business_customer_detail,
        name="api-business-customer-detail",
    ),
    path("inventory/warehouses/", inventory_warehouses, name="api-inventory-warehouses"),
    path("inventory/items/", inventory_items, name="api-inventory-items"),
    path("inventory/items/<int:item_id>/adjust/", inventory_adjust, name="api-inventory-adjust"),
    path("sales/quotes/", quotes, name="api-sales-quotes"),
    path("sales/quotes/<int:quote_id>/", quote_detail, name="api-sales-quote-detail"),
    path("sales/quotes/<int:quote_id>/files/", quote_files, name="api-sales-quote-files"),
    path("orders/", transaction_orders, name="api-transaction-orders"),
    path("orders/<int:order_id>/", transaction_order_detail, name="api-transaction-order-detail"),
    path("workflows/", workflows, name="api-transaction-workflows"),
    path("transactions/", transactions, name="api-transaction-history"),
    path("cms/pages/", pages, name="api-cms-pages"),
    path("cms/pages/<slug:slug>/", page_detail, name="api-cms-page-detail"),
    path("cms/menu/", menu, name="api-cms-menu"),
    path("newsletter/subscribers/", newsletter_subscribers, name="api-newsletter-subscribers"),
    path("auth/profile/", profile, name="api-auth-profile"),
    path("auth/permissions/", permissions, name="api-auth-permissions"),
    path("foundation/auth/login/", foundation_login, name="api-foundation-login"),
    path("foundation/auth/logout/", foundation_logout, name="api-foundation-logout"),
    path("foundation/users/", foundation_users, name="api-foundation-users"),
    path(
        "foundation/users/<int:user_id>/profile/",
        foundation_user_profile,
        name="api-foundation-user-profile",
    ),
    path("foundation/permissions/roles/", foundation_roles, name="api-foundation-roles"),
    path(
        "foundation/permissions/check/",
        foundation_permission_check,
        name="api-foundation-permission-check",
    ),
    path("public/home/", home, name="api-public-home"),
    path("news/", news, name="api-news"),
    path("openapi.json", openapi_schema, name="api-openapi-schema"),
    path("version/", version, name="api-version"),
    path("demo/aws/", aws_demo, name="api-demo-aws"),
    path("demo/external/weather/", external_weather, name="api-demo-external-weather"),
    path("ai/chat/", ai_chat, name="api-ai-chat"),
]
