"""Test cho Django Quotation module."""

import json

from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse

from customers.models import Customer, CustomerNote
from products.models import Material, Product, ProductCategory

from .models import QuoteFile, QuoteRequest, QuoteRequestItem
from .services import create_public_quote_request, filter_quotes, quote_detail_to_dict


class QuotationModuleTest(TransactionTestCase):
    """Kiểm tra service, transaction và API của module báo giá."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(Customer)
            schema_editor.create_model(CustomerNote)
            schema_editor.create_model(ProductCategory)
            schema_editor.create_model(Material)
            schema_editor.create_model(Product)
            schema_editor.create_model(QuoteRequest)
            schema_editor.create_model(QuoteRequestItem)
            schema_editor.create_model(QuoteFile)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(QuoteFile)
            schema_editor.delete_model(QuoteRequestItem)
            schema_editor.delete_model(QuoteRequest)
            schema_editor.delete_model(Product)
            schema_editor.delete_model(Material)
            schema_editor.delete_model(ProductCategory)
            schema_editor.delete_model(CustomerNote)
            schema_editor.delete_model(Customer)
        super().tearDownClass()

    def setUp(self):
        QuoteFile.objects.all().delete()
        QuoteRequestItem.objects.all().delete()
        QuoteRequest.objects.all().delete()
        Customer.objects.all().delete()
        self.customer = Customer.objects.create(
            company_name="Demo Precision",
            contact_name="Nguyen Van A",
            email="buyer@example.com",
            phone="0900000000",
            country="Vietnam",
        )
        self.quote = QuoteRequest.objects.create(
            customer=self.customer,
            project_name="Báo giá trục H-Series",
            message="Cần báo giá 100 chi tiết.",
            status=QuoteRequest.STATUS_NEW,
        )
        QuoteRequestItem.objects.create(
            quote_request=self.quote,
            drawing_code="H-SERIES-001",
            quantity=100,
            tolerance="±0.01mm",
            note="Cần kiểm tra độ đồng tâm.",
        )
        QuoteFile.objects.create(
            quote_request=self.quote,
            file_name="H-SERIES-001.pdf",
            file_url="/uploads/demo/H-SERIES-001.pdf",
            file_type="pdf",
        )

    def test_filter_quotes_returns_matching_project(self):
        results = filter_quotes(keyword="H-Series")

        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().customer.contact_name, "Nguyen Van A")

    def test_quote_detail_to_dict_includes_items_and_files(self):
        data = quote_detail_to_dict(QuoteRequest.objects.prefetch_related("items", "files").select_related("customer").get(id=self.quote.id))

        self.assertEqual(data["project_name"], "Báo giá trục H-Series")
        self.assertEqual(data["items"][0]["quantity"], 100)
        self.assertEqual(data["files"][0]["file_type"], "pdf")

    def test_create_public_quote_request_creates_related_records(self):
        quote = create_public_quote_request(
            {
                "name": "Tran Thi B",
                "email": "b@example.com",
                "product": "Fixture kiểm tra",
                "quantity": "5",
                "drawing_pdf": "/uploads/demo/fixture.pdf",
            }
        )

        self.assertEqual(quote.customer.contact_name, "Tran Thi B")
        self.assertEqual(quote.items.count(), 1)
        self.assertEqual(quote.files.count(), 1)

    def test_public_quote_create_api_returns_json(self):
        response = self.client.post(
            reverse("quotation:api-create"),
            data=json.dumps({"name": "Le Van C", "phone": "0911111111", "product": "Bánh răng"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["quote"]["items"][0]["drawing_code"], "Bánh răng")
