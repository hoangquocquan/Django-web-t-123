"""Read-only repository adapter for catalog products."""

from django.db.models import Prefetch

from apps.catalog.models import Product, ProductImage
from apps.catalog.repositories.base import LegacyCatalogRepository


class ProductRepository(LegacyCatalogRepository):
    """Access legacy products through the Django ORM read-only mapping."""

    model = Product

    def list_products(self):
        """Return all products with category joined from the legacy database."""
        return self.queryset().select_related("category").all()

    def list_products_with_images(self):
        """Return products and preload images to avoid N+1 queries in list views."""
        return self.list_products().prefetch_related(
            Prefetch("images", queryset=self.product_image_queryset())
        )

    def get_product(self, product_id):
        """Return one product by legacy ID."""
        return self.list_products().get(id=product_id)

    def product_image_queryset(self):
        """Create the base image QuerySet on the legacy database."""
        return ProductImage.objects.using(self.database_alias)

    def list_product_images(self, product_id):
        """Return images for a product from the legacy database."""
        return self.product_image_queryset().filter(product_id=product_id)
