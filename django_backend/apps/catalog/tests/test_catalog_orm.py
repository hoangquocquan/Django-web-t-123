"""Validation tests for Phase 4A read-only catalog ORM mappings."""

from django.db import connections
import pytest

from apps.catalog.models import Category, Product, ProductImage, ProductMaterial
from apps.catalog.repositories.category_repository import CategoryRepository
from apps.catalog.repositories.product_repository import ProductRepository
from apps.catalog.services.catalog_service import CatalogService


@pytest.fixture
def legacy_db(django_db_blocker):
    """Allow read-only access to the external legacy database without test DB setup."""
    with django_db_blocker.unblock():
        yield


def test_legacy_database_connection_reads_catalog_tables(legacy_db):
    """Django can connect to the legacy SQLite database and read metadata."""
    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]

    assert product_count >= 1


def test_product_model_table_mapping_matches_legacy_count(legacy_db):
    """The Product model maps to the existing products table."""
    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM products")
        direct_count = cursor.fetchone()[0]

    orm_count = Product.objects.using("legacy").count()

    assert orm_count == direct_count


def test_product_category_relationship_resolves(legacy_db):
    """Product -> Category foreign key resolves through the legacy alias."""
    product = Product.objects.using("legacy").select_related("category").first()

    assert product is not None
    assert product.category_id == product.category.id
    assert product.category.name


def test_explicit_relationship_table_uses_composite_key(legacy_db):
    """Composite junction tables remain explicit unmanaged relationship models."""
    relation = ProductMaterial.objects.using("legacy").first()

    assert relation is not None
    assert relation.product_id is not None
    assert relation.material_id is not None


def test_legacy_models_block_instance_save_and_delete(legacy_db):
    """Read-only models reject accidental instance writes."""
    product = Product.objects.using("legacy").first()

    with pytest.raises(RuntimeError):
        product.save()

    with pytest.raises(RuntimeError):
        product.delete()


def test_legacy_models_block_bulk_update_and_delete(legacy_db):
    """Read-only querysets reject accidental bulk writes."""
    queryset = Product.objects.using("legacy").filter(status="published")

    with pytest.raises(RuntimeError):
        queryset.update(status="draft")

    with pytest.raises(RuntimeError):
        queryset.delete()


def test_category_repository_reads_from_legacy_database(legacy_db):
    """CategoryRepository exposes read-only category queries."""
    repository = CategoryRepository()
    categories = list(repository.list_categories())

    assert categories
    assert all(isinstance(category, Category) for category in categories)


def test_product_repository_reads_images_from_legacy_database(legacy_db):
    """ProductRepository exposes product image lookup."""
    product = Product.objects.using("legacy").first()
    repository = ProductRepository()
    images = list(repository.list_product_images(product.id))

    assert all(isinstance(image, ProductImage) for image in images)


def test_catalog_service_uses_repository_for_product_detail(legacy_db):
    """CatalogService returns product detail through repository calls only."""
    product = Product.objects.using("legacy").first()
    service = CatalogService()

    detail = service.get_product_detail(product.id)

    assert detail["product"].id == product.id
    assert "images" in detail
