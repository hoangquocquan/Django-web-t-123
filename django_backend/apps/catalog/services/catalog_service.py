"""Catalog read-only service layer."""

from apps.catalog.repositories.category_repository import CategoryRepository
from apps.catalog.repositories.capability_repository import CapabilityRepository
from apps.catalog.repositories.material_repository import MaterialRepository
from apps.catalog.repositories.product_repository import ProductRepository


class CatalogService:
    """Read-only catalog service that depends on repository adapters only."""

    def __init__(
        self,
        product_repository=None,
        category_repository=None,
        capability_repository=None,
        material_repository=None,
    ):
        """Allow tests to pass a repository double later if needed."""
        self.product_repository = product_repository or ProductRepository()
        self.category_repository = category_repository or CategoryRepository()
        self.capability_repository = capability_repository or CapabilityRepository()
        self.material_repository = material_repository or MaterialRepository()

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

    def list_categories(self):
        """Return catalog categories through the repository boundary."""
        return self.category_repository.list_categories()

    def list_materials(self):
        """Return catalog materials through the repository boundary."""
        return self.material_repository.list_materials()

    def list_capabilities(self):
        """Return manufacturing capabilities through the repository boundary."""
        return self.capability_repository.list_capabilities()
