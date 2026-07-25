"""Catalog read-only service layer."""

from apps.catalog.repositories.product_repository import ProductRepository


class CatalogService:
    """Read-only catalog service that depends on repository adapters only."""

    def __init__(self, product_repository=None):
        """Allow tests to pass a repository double later if needed."""
        self.product_repository = product_repository or ProductRepository()

    def list_products(self):
        """Return products without business transformation in Phase 4A."""
        return self.product_repository.list_products()

    def get_product_detail(self, product_id):
        """Return a product and related images without business transformation."""
        product = self.product_repository.get_product(product_id)
        images = self.product_repository.list_product_images(product_id)
        return {
            "product": product,
            "images": images,
        }
