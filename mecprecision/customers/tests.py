"""Test cho Django Customers module.

Vì model đang dùng `managed = False`, test sẽ tự tạo bảng tạm trong database test.
Khi chuyển hẳn sang Django migration, phần tạo bảng thủ công này có thể bỏ đi.
"""

from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse

from .models import ContactRequest, Customer, CustomerNote, NewsletterSubscriber
from .services import customer_detail_to_dict, filter_contact_requests, filter_customers


class CustomerModuleTest(TransactionTestCase):
    """Kiểm tra model, service và API của Customers module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(Customer)
            schema_editor.create_model(ContactRequest)
            schema_editor.create_model(CustomerNote)
            schema_editor.create_model(NewsletterSubscriber)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(NewsletterSubscriber)
            schema_editor.delete_model(CustomerNote)
            schema_editor.delete_model(ContactRequest)
            schema_editor.delete_model(Customer)
        super().tearDownClass()

    def setUp(self):
        CustomerNote.objects.all().delete()
        Customer.objects.all()._raw_delete(Customer.objects.db)
        ContactRequest.objects.all().delete()
        NewsletterSubscriber.objects.all().delete()
        self.customer = Customer.objects.create(
            company_name="ABC Precision",
            contact_name="Nguyen Van A",
            email="a@example.com",
            phone="0900000001",
            country="Vietnam",
        )
        CustomerNote.objects.create(customer=self.customer, note="Đã gọi tư vấn lần 1.", created_by="admin")
        self.contact = ContactRequest.objects.create(
            name="Tran Thi B",
            contact="b@example.com",
            company="B Manufacturing",
            phone="0900000002",
            email="b@example.com",
            country="Japan",
            interested_product="Trục CNC",
            message="Cần tư vấn gia công trục chính xác.",
            status=ContactRequest.STATUS_NEW,
            is_read=False,
        )

    def test_filter_customers_returns_matching_company(self):
        results = filter_customers(keyword="ABC")

        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().contact_name, "Nguyen Van A")

    def test_contact_filter_returns_matching_product_interest(self):
        results = filter_contact_requests(keyword="Trục CNC")

        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().name, "Tran Thi B")

    def test_customer_detail_to_dict_includes_notes(self):
        data = customer_detail_to_dict(Customer.objects.prefetch_related("notes").get(id=self.customer.id))

        self.assertEqual(data["company_name"], "ABC Precision")
        self.assertEqual(data["notes"][0]["note"], "Đã gọi tư vấn lần 1.")

    def test_contact_request_list_api_returns_json(self):
        response = self.client.get(reverse("customers:api-contact-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["interested_product"], "Trục CNC")
