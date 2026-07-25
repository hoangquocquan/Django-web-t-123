"""Read-only unmanaged ORM models for the legacy catalog tables."""

from django.db import models

from apps.common.models import LegacyReadOnlyModel


class Category(LegacyReadOnlyModel):
    """Legacy product category."""

    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    slug = models.TextField(unique=True)
    description = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.TextField()

    class Meta:
        managed = False
        db_table = "product_categories"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name


class Material(LegacyReadOnlyModel):
    """Legacy manufacturing material."""

    id = models.IntegerField(primary_key=True)
    name = models.TextField(unique=True)
    standard = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "materials"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Machine(LegacyReadOnlyModel):
    """Legacy manufacturing machine."""

    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    machine_type = models.TextField()
    brand = models.TextField(blank=True, null=True)
    max_size = models.TextField(blank=True, null=True)
    tolerance = models.TextField(blank=True, null=True)
    status = models.TextField(default="active")

    class Meta:
        managed = False
        db_table = "machines"
        ordering = ["id"]

    def __str__(self):
        return self.name


class ManufacturingProcess(LegacyReadOnlyModel):
    """Legacy manufacturing process."""

    id = models.IntegerField(primary_key=True)
    name = models.TextField(unique=True)
    description = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "manufacturing_processes"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name


class Capability(LegacyReadOnlyModel):
    """Legacy manufacturing capability."""

    id = models.IntegerField(primary_key=True)
    title = models.TextField()
    content = models.TextField()
    icon_label = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.TextField()

    class Meta:
        managed = False
        db_table = "capabilities"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class Product(LegacyReadOnlyModel):
    """Legacy product catalog item."""

    id = models.IntegerField(primary_key=True)
    category = models.ForeignKey(
        Category,
        db_column="category_id",
        on_delete=models.DO_NOTHING,
        related_name="products",
    )
    name = models.TextField()
    slug = models.TextField(unique=True)
    short_description = models.TextField()
    description = models.TextField()
    main_image = models.TextField()
    is_featured = models.BooleanField(default=False)
    created_at = models.TextField()
    updated_at = models.TextField()
    thumbnail_url = models.TextField(blank=True, null=True)
    gallery_urls = models.TextField(blank=True, null=True)
    tags_text = models.TextField(blank=True, null=True)
    seo_title = models.TextField(blank=True, null=True)
    seo_description = models.TextField(blank=True, null=True)
    related_product_ids = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    status = models.TextField(default="published")
    sku = models.TextField(blank=True, null=True)
    price = models.FloatField(default=0)
    pdf_url = models.TextField(blank=True, null=True)
    video_url = models.TextField(blank=True, null=True)
    seo_keywords = models.TextField(blank=True, null=True)
    canonical_url = models.TextField(blank=True, null=True)
    og_image = models.TextField(blank=True, null=True)
    robots = models.TextField(default="index,follow")
    schema_json = models.TextField(blank=True, null=True)
    published_at = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "products"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name


class ProductImage(LegacyReadOnlyModel):
    """Legacy product gallery image."""

    id = models.IntegerField(primary_key=True)
    product = models.ForeignKey(
        Product,
        db_column="product_id",
        on_delete=models.CASCADE,
        related_name="images",
    )
    image_url = models.TextField()
    alt_text = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "product_images"
        ordering = ["sort_order", "id"]


class ProductSpec(LegacyReadOnlyModel):
    """Legacy product technical specification."""

    id = models.IntegerField(primary_key=True)
    product = models.ForeignKey(
        Product,
        db_column="product_id",
        on_delete=models.CASCADE,
        related_name="specs",
    )
    spec_name = models.TextField()
    spec_value = models.TextField()
    unit = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "product_specs"
        ordering = ["sort_order", "id"]


class ProductMaterial(LegacyReadOnlyModel):
    """Legacy product-to-material relationship table."""

    pk = models.CompositePrimaryKey("product", "material")
    product = models.ForeignKey(Product, db_column="product_id", on_delete=models.CASCADE)
    material = models.ForeignKey(Material, db_column="material_id", on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = "product_materials"


class ProductProcess(LegacyReadOnlyModel):
    """Legacy product-to-process relationship table with workflow metadata."""

    pk = models.CompositePrimaryKey("product", "process")
    product = models.ForeignKey(Product, db_column="product_id", on_delete=models.CASCADE)
    process = models.ForeignKey(
        ManufacturingProcess,
        db_column="process_id",
        on_delete=models.CASCADE,
    )
    step_order = models.IntegerField(default=0)
    note = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "product_processes"
        ordering = ["step_order"]


class CapabilityMachine(LegacyReadOnlyModel):
    """Legacy capability-to-machine relationship table."""

    pk = models.CompositePrimaryKey("capability", "machine")
    capability = models.ForeignKey(Capability, db_column="capability_id", on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine, db_column="machine_id", on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = "capability_machines"
