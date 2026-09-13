"""Collision-free URL namespace for Phase 4A canonical read APIs."""

from django.urls import path

from apps.api.views.canonical import (
    ApprovalDecisionListView,
    CustomerDecisionListView,
    CustomerDetailView,
    CustomerListView,
    EntityAuditTimelineView,
    GlobalAuditListView,
    MaterialDetailView,
    MaterialListView,
    OrderDetailView,
    OrderLineListView,
    OrderListView,
    OrderProgressListView,
    PartDetailView,
    PartListView,
    QuotationDetailView,
    QuotationFamilyDetailView,
    QuotationFamilyListView,
    QuotationLineListView,
    QuotationListView,
    QuotationRevisionListView,
    RfqDetailView,
    RfqDocumentListView,
    RfqLineListView,
    RfqListView,
    TechnicalReviewListView,
)


urlpatterns = [
    path("customers/", CustomerListView.as_view(), name="canonical-customer-list"),
    path(
        "customers/<int:object_id>/",
        CustomerDetailView.as_view(),
        name="canonical-customer-detail",
    ),
    path("parts/", PartListView.as_view(), name="canonical-part-list"),
    path(
        "parts/<int:object_id>/",
        PartDetailView.as_view(),
        name="canonical-part-detail",
    ),
    path("materials/", MaterialListView.as_view(), name="canonical-material-list"),
    path(
        "materials/<int:object_id>/",
        MaterialDetailView.as_view(),
        name="canonical-material-detail",
    ),
    path("rfqs/", RfqListView.as_view(), name="canonical-rfq-list"),
    path("rfqs/<int:rfq_id>/", RfqDetailView.as_view(), name="canonical-rfq-detail"),
    path(
        "rfqs/<int:rfq_id>/lines/",
        RfqLineListView.as_view(),
        name="canonical-rfq-lines",
    ),
    path(
        "rfqs/<int:rfq_id>/documents/",
        RfqDocumentListView.as_view(),
        name="canonical-rfq-documents",
    ),
    path(
        "rfqs/<int:rfq_id>/technical-reviews/",
        TechnicalReviewListView.as_view(),
        name="canonical-rfq-technical-reviews",
    ),
    path(
        "quotation-families/",
        QuotationFamilyListView.as_view(),
        name="canonical-quotation-family-list",
    ),
    path(
        "quotation-families/<str:family_number>/",
        QuotationFamilyDetailView.as_view(),
        name="canonical-quotation-family-detail",
    ),
    path(
        "quotation-families/<str:family_number>/revisions/",
        QuotationRevisionListView.as_view(),
        name="canonical-quotation-revisions",
    ),
    path("quotations/", QuotationListView.as_view(), name="canonical-quotation-list"),
    path(
        "quotations/<int:quotation_id>/",
        QuotationDetailView.as_view(),
        name="canonical-quotation-detail",
    ),
    path(
        "quotations/<int:quotation_id>/lines/",
        QuotationLineListView.as_view(),
        name="canonical-quotation-lines",
    ),
    path(
        "quotations/<int:quotation_id>/approval-decisions/",
        ApprovalDecisionListView.as_view(),
        name="canonical-quotation-approval-decisions",
    ),
    path(
        "quotations/<int:quotation_id>/customer-decisions/",
        CustomerDecisionListView.as_view(),
        name="canonical-quotation-customer-decisions",
    ),
    path("orders/", OrderListView.as_view(), name="canonical-order-list"),
    path(
        "orders/<int:order_id>/",
        OrderDetailView.as_view(),
        name="canonical-order-detail",
    ),
    path(
        "orders/<int:order_id>/lines/",
        OrderLineListView.as_view(),
        name="canonical-order-lines",
    ),
    path(
        "orders/<int:order_id>/progress/",
        OrderProgressListView.as_view(),
        name="canonical-order-progress",
    ),
    path(
        "timelines/<str:entity_type>/<int:entity_id>/",
        EntityAuditTimelineView.as_view(),
        name="canonical-entity-audit-timeline",
    ),
    path(
        "audit-events/",
        GlobalAuditListView.as_view(),
        name="canonical-global-audit-list",
    ),
]
