"""Kiểm tra Django luôn đọc catalog qua database alias `legacy`.

Các test này bảo vệ nguyên tắc migration quan trọng:
Django chỉ đọc database cũ, không ghi và không trộn nhầm sang database mặc định.
"""

import pytest

from apps.catalog.models import Product, ProductMaterial
from apps.catalog.repositories.category_repository import CategoryRepository
from apps.catalog.repositories.product_repository import ProductRepository


def test_product_repository_queryset_uses_legacy_alias(legacy_db):
    """Repository sản phẩm phải tạo QuerySet trên alias `legacy`."""
    queryset = ProductRepository().list_products()

    assert queryset._db == "legacy"


def test_category_repository_queryset_uses_legacy_alias(legacy_db):
    """Repository danh mục phải tạo QuerySet trên alias `legacy`."""
    queryset = CategoryRepository().list_categories()

    assert queryset._db == "legacy"


def test_product_image_repository_queryset_uses_legacy_alias(legacy_db):
    """Query ảnh sản phẩm cũng phải đọc từ database legacy."""
    product = Product.objects.using("legacy").first()
    queryset = ProductRepository().list_product_images(product.id)

    assert queryset._db == "legacy"


def test_legacy_database_fixture_is_read_only(legacy_db):
    """Bản copy test được mở bằng mode read-only giống cấu hình production migration."""
    product = Product.objects.using("legacy").first()

    with pytest.raises(RuntimeError):
        product.save()


def test_composite_relationship_can_access_related_models(legacy_db):
    """Bảng quan hệ composite vẫn truy cập được Product và Material liên quan."""
    relation = ProductMaterial.objects.using("legacy").select_related("product", "material").first()

    assert relation is not None
    assert relation.product.id == relation.product_id
    assert relation.material.id == relation.material_id
