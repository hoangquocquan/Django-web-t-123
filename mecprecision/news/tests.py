"""Test cho Django News module."""

from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from .models import NewsArticle, NewsCategory, NewsTag, Tag
from .services import filter_news, get_public_news, news_detail_to_dict


class NewsModuleTest(TransactionTestCase):
    """Kiểm tra service và API của module tin tức."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(NewsCategory)
            schema_editor.create_model(Tag)
            schema_editor.create_model(NewsArticle)
            schema_editor.create_model(NewsTag)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(NewsTag)
            schema_editor.delete_model(NewsArticle)
            schema_editor.delete_model(Tag)
            schema_editor.delete_model(NewsCategory)
        super().tearDownClass()

    def setUp(self):
        NewsTag.objects.all().delete()
        NewsArticle.objects.all().delete()
        Tag.objects.all().delete()
        NewsCategory.objects.all().delete()
        self.category = NewsCategory.objects.create(name="Kỹ thuật", slug="ky-thuat")
        self.article = NewsArticle.objects.create(
            category=self.category,
            title="Tối ưu gia công CNC",
            slug="toi-uu-gia-cong-cnc",
            image="https://example.com/cnc.jpg",
            description="Cách tối ưu quy trình gia công CNC.",
            content="Nội dung bài viết kỹ thuật.",
            tags_text="cnc, quy trình",
            seo_title="SEO CNC",
            seo_description="Mô tả SEO CNC",
            author="MecPrecision Editorial",
            status=NewsArticle.STATUS_PUBLISHED,
            published_at=timezone.now(),
        )
        NewsArticle.objects.create(
            category=self.category,
            title="Bài nháp nội bộ",
            slug="bai-nhap-noi-bo",
            image="https://example.com/draft.jpg",
            description="Bài chưa xuất bản.",
            status=NewsArticle.STATUS_DRAFT,
            published_at=timezone.now(),
        )

    def test_public_news_excludes_draft(self):
        results = get_public_news()

        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().title, "Tối ưu gia công CNC")

    def test_filter_news_searches_tags_text(self):
        results = filter_news(keyword="quy trình", public_only=True)

        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().slug, "toi-uu-gia-cong-cnc")

    def test_news_detail_to_dict_includes_seo(self):
        data = news_detail_to_dict(self.article)

        self.assertEqual(data["seo_title"], "SEO CNC")
        self.assertEqual(data["category"], "Kỹ thuật")

    def test_news_list_api_returns_json(self):
        response = self.client.get(reverse("news:api-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["title"], "Tối ưu gia công CNC")
