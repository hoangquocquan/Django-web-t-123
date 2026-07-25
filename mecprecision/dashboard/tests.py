"""Test cho Django Dashboard module."""

from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse

from .models import PageVisit
from .services import get_dashboard_stats, track_page_visit


class DashboardModuleTest(TransactionTestCase):
    """Kiểm tra dashboard đọc số liệu và ghi visit."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(PageVisit)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(PageVisit)
        super().tearDownClass()

    def setUp(self):
        PageVisit.objects.all().delete()

    def test_track_page_visit_creates_row(self):
        track_page_visit("/san-pham")

        self.assertEqual(PageVisit.objects.count(), 1)

    def test_dashboard_stats_contains_charts(self):
        track_page_visit("/")
        stats = get_dashboard_stats()

        self.assertEqual(stats["counts"]["visits"], 1)
        self.assertEqual(len(stats["charts"]["7_days"]), 7)

    def test_dashboard_api_returns_json(self):
        response = self.client.get(reverse("dashboard:api"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("counts", response.json())
