"""SEO-compatible public website URLs."""

from django.urls import path

from . import views


app_name = "website"

urlpatterns = [
    path("", views.home, name="home"),
    path("products", views.products, name="products-no-slash"),
    path("products/", views.products, name="products"),
    path("product/<slug:slug>", views.product_detail, name="product-detail-no-slash"),
    path("product/<slug:slug>/", views.product_detail, name="product-detail"),
    path("technology", views.technology, name="technology-no-slash"),
    path("technology/", views.technology, name="technology"),
    path("news", views.news, name="news-no-slash"),
    path("news/", views.news, name="news"),
    path("news/<slug:slug>", views.news_detail, name="news-detail-no-slash"),
    path("news/<slug:slug>/", views.news_detail, name="news-detail"),
    path("contact", views.contact, name="contact-no-slash"),
    path("contact/", views.contact, name="contact"),
    path("api/home", views.api_home, name="api-home-no-slash"),
    path("api/home/", views.api_home, name="api-home"),
]
