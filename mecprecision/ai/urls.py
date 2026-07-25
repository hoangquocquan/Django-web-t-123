"""URL của module AI.

Nhóm URL này được gắn dưới `/ai/` từ file `core/urls.py`.
"""

from django.urls import path

from . import views

app_name = "ai"

urlpatterns = [
    path("", views.ai_home, name="home"),
    path("api/status/", views.status_api, name="api-status"),
    path("api/chat/", views.chat_api, name="api-chat"),
    path("api/translate/", views.translate_api, name="api-translate"),
    path("api/developer/", views.developer_api, name="api-developer"),
    path("api/product-content/", views.product_content_api, name="api-product-content"),
    path("api/contacts-summary/", views.contacts_summary_api, name="api-contacts-summary"),
    path("api/quote-analysis/", views.quote_analysis_api, name="api-quote-analysis"),
    path("api/smart-search/", views.smart_search_api, name="api-smart-search"),
    path("api/dashboard-insights/", views.dashboard_insights_api, name="api-dashboard-insights"),
]
