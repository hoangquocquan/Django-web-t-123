"""URL routing cho giao dien Sales, CRM va AI Sales."""

from django.urls import path

from . import views


app_name = "business_ui"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("leads/", views.lead_pipeline, name="lead-pipeline"),
    path("customers/", views.customers, name="customers"),
    path("customers/<int:customer_id>/", views.customer_detail, name="customer-detail"),
    path("quotations/", views.quotations, name="quotations"),
    path("quotations/<int:quotation_id>/", views.quotation_detail, name="quotation-detail"),
    path("ai-sales/", views.ai_sales_assistant, name="ai-sales"),
    path("documents/", views.document_intelligence, name="documents"),
]
