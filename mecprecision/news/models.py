"""Django models cho module News.

Các model này map vào bảng tin tức cũ của SQLite:
- `news_categories`: danh mục bài viết.
- `news`: bài viết.
- `tags`: tag dùng để lọc/tìm kiếm nội dung.
- `news_tags`: bảng nối giữa bài viết và tag.
"""

from django.db import models
from django.utils import timezone


class NewsCategory(models.Model):
    """Danh mục tin tức, ví dụ: Tin nhà máy, Kỹ thuật, Công nghệ."""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        managed = False
        db_table = "news_categories"
        ordering = ["id"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tag giúp nhóm bài viết theo chủ đề nhỏ hơn danh mục."""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        managed = False
        db_table = "tags"
        ordering = ["name"]

    def __str__(self):
        return self.name


class NewsArticle(models.Model):
    """Bài viết tin tức của website."""

    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Nháp"),
        (STATUS_PUBLISHED, "Đã xuất bản"),
        (STATUS_ARCHIVED, "Lưu trữ"),
    ]

    category = models.ForeignKey(NewsCategory, on_delete=models.PROTECT, db_column="category_id")
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    image = models.TextField()
    description = models.TextField()
    content = models.TextField(blank=True, null=True)
    tags_text = models.TextField(blank=True, null=True)
    seo_title = models.CharField(max_length=255, blank=True, null=True)
    seo_description = models.TextField(blank=True, null=True)
    thumbnail_url = models.TextField(blank=True, null=True)
    author = models.CharField(max_length=255, blank=True, null=True)
    published_at = models.DateTimeField(default=timezone.now)
    scheduled_at = models.DateTimeField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PUBLISHED)

    class Meta:
        managed = False
        db_table = "news"
        ordering = ["-published_at", "-id"]

    def __str__(self):
        return self.title


class NewsTag(models.Model):
    """Bảng nối bài viết với tag.

    SQLite cũ dùng khóa chính kép (`news_id`, `tag_id`). Django chưa dùng model
    này cho CRUD chính ở giai đoạn này; model chỉ giúp đọc dữ liệu và test đơn giản.
    """

    news = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, db_column="news_id")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, db_column="tag_id")

    class Meta:
        managed = False
        db_table = "news_tags"
        unique_together = ("news", "tag")
