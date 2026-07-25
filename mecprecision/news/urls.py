"""URL của module News.

Nhóm URL này được gắn dưới `/news/` từ file `core/urls.py`.
"""

from django.urls import path

from . import views

app_name = "news"

urlpatterns = [
    path("", views.news_list, name="list"),
    path("<int:news_id>/", views.news_detail, name="detail"),
    path("api/", views.news_list_api, name="api-list"),
    path("api/<int:news_id>/", views.news_detail_api, name="api-detail"),
]
