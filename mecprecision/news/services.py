"""Service layer cho News.

Service gom query tin tức vào một nơi để view không phải biết chi tiết database.
Đây là lớp tương đương `news_service.py` ở backend cũ nhưng viết theo Django ORM.
"""

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify

from .models import NewsArticle, NewsCategory


def get_news_categories():
    """Lấy toàn bộ danh mục tin tức."""
    return NewsCategory.objects.all()


def get_public_news():
    """Lấy bài đã published và đã tới lịch đăng."""
    now = timezone.now()
    return (
        NewsArticle.objects.select_related("category")
        .filter(status=NewsArticle.STATUS_PUBLISHED)
        .filter(Q(scheduled_at__isnull=True) | Q(scheduled_at__lte=now))
        .order_by("-published_at", "-id")
    )


def filter_news(keyword="", category_id=0, status="", sort="newest", public_only=False):
    """Lọc bài viết theo từ khóa, danh mục, trạng thái và kiểu sắp xếp."""
    queryset = get_public_news() if public_only else NewsArticle.objects.select_related("category")
    keyword = str(keyword or "").strip()
    if keyword:
        queryset = queryset.filter(
            Q(title__icontains=keyword)
            | Q(description__icontains=keyword)
            | Q(content__icontains=keyword)
            | Q(tags_text__icontains=keyword)
            | Q(category__name__icontains=keyword)
        )
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    if status:
        queryset = queryset.filter(status=status)

    sort_map = {
        "oldest": "published_at",
        "title": "title",
        "featured": "-is_featured",
    }
    return queryset.order_by(sort_map.get(sort, "-published_at"), "-id")


def paginate_news(queryset, page=1, per_page=10):
    """Phân trang danh sách tin tức."""
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page)


def get_news_detail(news_id, public_only=True):
    """Lấy chi tiết bài viết hoặc trả 404 nếu không tồn tại."""
    queryset = get_public_news() if public_only else NewsArticle.objects.select_related("category")
    return get_object_or_404(queryset, id=news_id)


def normalize_news_payload(payload):
    """Chuẩn hóa payload trước khi tạo/cập nhật tin tức bằng Django service."""
    title = str(payload.get("title", "")).strip()
    description = str(payload.get("description", "")).strip()
    image = str(payload.get("image", "")).strip()
    category_id = int(payload.get("category_id", 0) or 0)
    status = str(payload.get("status", NewsArticle.STATUS_PUBLISHED)).strip() or NewsArticle.STATUS_PUBLISHED
    if not category_id or not title or not image or not description:
        raise ValueError("Cần nhập danh mục, tiêu đề, ảnh và mô tả tin tức.")
    if status not in {NewsArticle.STATUS_DRAFT, NewsArticle.STATUS_PUBLISHED, NewsArticle.STATUS_ARCHIVED}:
        raise ValueError("Status tin tức chỉ được là draft, published hoặc archived.")

    return {
        "category_id": category_id,
        "title": title,
        "slug": str(payload.get("slug", "")).strip() or slugify(title),
        "image": image,
        "description": description,
        "content": str(payload.get("content", "")).strip(),
        "tags_text": str(payload.get("tags_text", "")).strip(),
        "seo_title": str(payload.get("seo_title", title)).strip(),
        "seo_description": str(payload.get("seo_description", description)).strip(),
        "thumbnail_url": str(payload.get("thumbnail_url", image)).strip() or image,
        "author": str(payload.get("author", "MecPrecision Editorial")).strip(),
        "published_at": payload.get("published_at") or timezone.now(),
        "scheduled_at": payload.get("scheduled_at") or None,
        "is_featured": bool(payload.get("is_featured", False)),
        "status": status,
    }


def create_news(payload):
    """Tạo bài viết mới từ payload đã chuẩn hóa."""
    data = normalize_news_payload(payload)
    return NewsArticle.objects.create(**data)


def news_to_dict(article):
    """Đổi NewsArticle model thành dict ngắn để trả JSON danh sách."""
    return {
        "id": article.id,
        "title": article.title,
        "slug": article.slug,
        "image": article.image,
        "thumbnail_url": article.thumbnail_url,
        "description": article.description,
        "category": article.category.name,
        "author": article.author,
        "published_at": article.published_at,
        "scheduled_at": article.scheduled_at,
        "is_featured": article.is_featured,
        "status": article.status,
    }


def news_detail_to_dict(article):
    """Đổi chi tiết bài viết thành dict đầy đủ hơn cho API."""
    data = news_to_dict(article)
    data.update(
        {
            "content": article.content,
            "tags_text": article.tags_text,
            "seo_title": article.seo_title,
            "seo_description": article.seo_description,
        }
    )
    return data
