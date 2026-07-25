"""Test cho Django Common/System module."""

from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse

from .models import CmsBanner, CmsMenuItem, CmsPage, EnterpriseEvent, JobQueue, Notification
from .services import enqueue_job, health_check, publish_event


class CommonModuleTest(TransactionTestCase):
    """Kiểm tra health check, pages và queue/event."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(CmsPage)
            schema_editor.create_model(CmsMenuItem)
            schema_editor.create_model(CmsBanner)
            schema_editor.create_model(EnterpriseEvent)
            schema_editor.create_model(JobQueue)
            schema_editor.create_model(Notification)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(Notification)
            schema_editor.delete_model(JobQueue)
            schema_editor.delete_model(EnterpriseEvent)
            schema_editor.delete_model(CmsBanner)
            schema_editor.delete_model(CmsMenuItem)
            schema_editor.delete_model(CmsPage)
        super().tearDownClass()

    def setUp(self):
        Notification.objects.all().delete()
        JobQueue.objects.all().delete()
        EnterpriseEvent.objects.all().delete()
        CmsBanner.objects.all().delete()
        CmsMenuItem.objects.all().delete()
        CmsPage.objects.all().delete()

    def test_health_check_is_ok(self):
        self.assertEqual(health_check()["status"], "ok")

    def test_event_and_job_are_created(self):
        publish_event("quote.created", "quote_request", 1, {"project": "Demo"})
        enqueue_job("backup.database", {"manual": True})

        self.assertEqual(EnterpriseEvent.objects.count(), 1)
        self.assertEqual(JobQueue.objects.count(), 1)

    def test_pages_api_returns_published_pages(self):
        CmsPage.objects.create(title="About", slug="about", status="published")
        response = self.client.get(reverse("common:api-pages"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["slug"], "about")
