"""Test các pattern truy vấn catalog để tránh lỗi N+1 khi mở rộng."""

from apps.catalog.repositories.product_repository import ProductRepository
from apps.catalog.services.catalog_service import CatalogService


def test_list_products_selects_category_in_one_query(legacy_db, django_assert_num_queries):
    """Danh sách sản phẩm kèm danh mục chỉ nên cần một query."""
    repository = ProductRepository()

    with django_assert_num_queries(1, using="legacy"):
        products = list(repository.list_products()[:5])
        category_names = [product.category.name for product in products]

    assert products
    assert all(category_names)


def test_list_products_with_images_prefetches_images(legacy_db, django_assert_num_queries):
    """Danh sách sản phẩm kèm ảnh dùng prefetch để tránh query lặp theo từng sản phẩm."""
    repository = ProductRepository()

    with django_assert_num_queries(2, using="legacy"):
        products = list(repository.list_products_with_images()[:5])
        image_groups = [list(product.images.all()) for product in products]

    assert products
    assert len(image_groups) == len(products)


def test_catalog_service_can_use_repository_double_without_orm():
    """Service phụ thuộc repository, nên sau này dễ test mà không cần database."""

    class FakeProductRepository:
        """Repository giả để chứng minh service không tự gọi ORM."""

        def list_products(self):
            return ["product-a"]

        def get_product(self, product_id):
            return {"id": product_id}

        def list_product_images(self, product_id):
            return [f"image-for-{product_id}"]

    service = CatalogService(product_repository=FakeProductRepository())

    assert service.list_products() == ["product-a"]
    assert service.get_product_detail(10) == {
        "product": {"id": 10},
        "images": ["image-for-10"],
    }


def test_catalog_service_product_detail_has_stable_query_count(
    legacy_db,
    django_assert_num_queries,
):
    """Chi tiết sản phẩm hiện cần một query cho product và một query cho images."""
    repository = ProductRepository()
    product = repository.list_products().first()
    service = CatalogService(product_repository=repository)

    with django_assert_num_queries(2, using="legacy"):
        detail = service.get_product_detail(product.id)
        images = list(detail["images"])

    assert detail["product"].id == product.id
    assert isinstance(images, list)
