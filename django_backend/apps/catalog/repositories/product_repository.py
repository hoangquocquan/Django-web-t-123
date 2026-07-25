"""Read-only repository adapter for catalog products."""

from apps.catalog.models import Product, ProductImage


class ProductRepository:
    """Access legacy products through the Django ORM read-only mapping."""

    database_alias = "legacy"

    def list_products(self):
        """Return all products with category joined from the legacy database."""
        return Product.objects.using(self.database_alias).select_related("category").all()

    def get_product(self, product_id):
        """Return one product by legacy ID."""
        return (
            Product.objects.using(self.database_alias)
            .select_related("category")
            .get(id=product_id)
        )

    def list_product_images(self, product_id):
        """Return images for a product from the legacy database."""
        return ProductImage.objects.using(self.database_alias).filter(product_id=product_id)
