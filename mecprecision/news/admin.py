"""Cấu hình Django Admin cho module News."""

from django.contrib import admin

from .models import NewsArticle, NewsCategory, Tag


@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    """Màn hình quản trị danh mục tin tức."""

    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Màn hình quản trị tag tin tức."""

    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    """Màn hình quản trị bài viết tin tức."""

    list_display = ("id", "title", "category", "author", "status", "is_featured", "published_at")
    search_fields = ("title", "description", "content", "tags_text", "author")
    list_filter = ("category", "status", "is_featured")
    prepopulated_fields = {"slug": ("title",)}
