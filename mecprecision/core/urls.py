"""URL gốc của Django skeleton.

Hiện tại chỉ nối admin và các app rỗng. Business logic sẽ được chuyển ở giai đoạn sau.
"""

from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("products/", include("products.urls")),
    path("customers/", include("customers.urls")),
    path("quotation/", include("quotation.urls")),
    path("news/", include("news.urls")),
    path("chatbot/", include("chatbot.urls")),
    path("ai/", include("ai.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("common/", include("common.urls")),
]
