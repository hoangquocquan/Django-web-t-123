"""Test cho Django Product module.

Test tự tạo bảng tạm vì models đang map bảng SQLite cũ với `managed = False`.
"""

from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse

from .models import (
    ManufacturingProcess,
    Material,
    Product,
    ProductCategory,
    ProductImage,
    ProductMaterial,
    ProductProcess,
    ProductSpec,
)
from .services import filter_products, product_detail_to_dict


class ProductModuleTest(TransactionTestCase):
    """Kiểm tra model, service và API của Product module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(ProductCategory)
            schema_editor.create_model(Material)
            schema_editor.create_model(ManufacturingProcess)
            schema_editor.create_model(Product)
            schema_editor.create_model(ProductMaterial)
            schema_editor.create_model(ProductProcess)
            schema_editor.create_model(ProductImage)
            schema_editor.create_model(ProductSpec)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(ProductSpec)
            schema_editor.delete_model(ProductImage)
            schema_editor.delete_model(ProductProcess)
            schema_editor.delete_model(ProductMaterial)
            schema_editor.delete_model(Product)
            schema_editor.delete_model(ManufacturingProcess)
            schema_editor.delete_model(Material)
            schema_editor.delete_model(ProductCategory)
        super().tearDownClass()

    def setUp(self):
        ProductSpec.objects.all().delete()
        ProductImage.objects.all().delete()
        Product.objects.all()._raw_delete(Product.objects.db)
        ProductCategory.objects.all().delete()
        self.category = ProductCategory.objects.create(
            name="Trục chính xác",
            slug="truc-chinh-xac",
            description="Danh mục trục CNC",
            sort_order=1,
        )
        self.product = Product.objects.create(
            category=self.category,
            name="Trục CNC H-Series",
            slug="truc-cnc-h-series",
            short_description="Trục CNC chính xác cao.",
            description="Gia công trục CNC theo bản vẽ kỹ thuật.",
            main_image="https://example.com/shaft.jpg",
            sku="SHAFT-H",
            price=100,
            status=Product.STATUS_PUBLISHED,
            sort_order=1,
        )
        ProductSpec.objects.create(product=self.product, spec_name="Dung sai", spec_value="0.01", unit="mm")
        ProductImage.objects.create(product=self.product, image_url="https://example.com/shaft-2.jpg", alt_text="Ảnh phụ")

    def test_filter_products_returns_published_items(self):
        results = filter_products(keyword="H-Series", status=Product.STATUS_PUBLISHED)

        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().name, "Trục CNC H-Series")

    def test_product_detail_to_dict_includes_specs_and_images(self):
        data = product_detail_to_dict(Product.objects.prefetch_related("images", "specs").get(id=self.product.id))

        self.assertEqual(data["name"], "Trục CNC H-Series")
        self.assertEqual(data["specs"][0]["name"], "Dung sai")
        self.assertEqual(data["images"][0]["alt"], "Ảnh phụ")

    def test_product_list_api_returns_json(self):
        response = self.client.get(reverse("products:api-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["sku"], "SHAFT-H")
