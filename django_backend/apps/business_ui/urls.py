"""URL routing cho giao dien Sales, CRM va AI Sales."""

from django.urls import path

from . import views

app_name = "business_ui"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("leads/", views.lead_pipeline, name="lead-pipeline"),
    path("leads/create/", views.lead_create, name="lead-create"),
    path(
        "leads/<int:lead_id>/transition/", views.lead_transition, name="lead-transition"
    ),
    path("leads/<int:lead_id>/assign/", views.lead_assign, name="lead-assign"),
    path(
        "leads/<int:lead_id>/opportunities/create/",
        views.opportunity_create,
        name="opportunity-create",
    ),
    path(
        "leads/<int:lead_id>/follow-ups/create/",
        views.follow_up_create,
        name="follow-up-create",
    ),
    path("customers/", views.customers, name="customers"),
    path("customers/<int:customer_id>/", views.customer_detail, name="customer-detail"),
    path(
        "customers/<int:customer_id>/interactions/create/",
        views.customer_interaction_create,
        name="customer-interaction-create",
    ),
    path(
        "customers/<int:customer_id>/notes/create/",
        views.customer_note_create,
        name="customer-note-create",
    ),
    path(
        "customers/<int:customer_id>/tasks/create/",
        views.customer_task_create,
        name="customer-task-create",
    ),
    path("quotations/", views.quotations, name="quotations"),
    path("quotations/create/", views.quotation_create, name="quotation-create"),
    path(
        "quotations/<int:quotation_id>/",
        views.quotation_detail,
        name="quotation-detail",
    ),
    path(
        "quotations/<int:quotation_id>/approve/",
        views.quotation_approve,
        name="quotation-approve",
    ),
    path(
        "quotations/<int:quotation_id>/handoff/",
        views.quotation_handoff,
        name="quotation-handoff",
    ),
    path("ai-sales/", views.ai_sales_assistant, name="ai-sales"),
    path("documents/", views.document_intelligence, name="documents"),
]
