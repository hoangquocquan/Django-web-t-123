"""URL routing for the Django-owned browser admin UI."""

from django.urls import path

from . import views


app_name = "admin_ui"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("products/", views.products, name="products"),
    path("products/<int:product_id>/", views.product_detail, name="product-detail"),
    path("customers/", views.customers, name="customers"),
    path("customers/<int:customer_id>/", views.customer_detail, name="customer-detail"),
    path("inventory/", views.inventory, name="inventory"),
    path("inventory/items/<int:item_id>/adjust/", views.inventory_adjust, name="inventory-adjust"),
    path("orders/", views.orders, name="orders"),
    path("orders/<int:order_id>/", views.order_detail, name="order-detail"),
    path("workflows/", views.workflows, name="workflows"),
    path("transactions/", views.transactions, name="transactions"),
]
