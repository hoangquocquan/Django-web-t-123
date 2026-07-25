"""Django models cho module Products.

Giai đoạn 4 dùng các model này để map sang bảng SQLite hiện có.
`managed = False` nghĩa là Django đọc/ghi bảng cũ, chưa tự tạo/xóa bảng bằng migration.
"""

from django.db import models


class ProductCategory(models.Model):
    """Danh mục sản phẩm, ví dụ: trục, bánh răng, cụm lắp ráp."""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "product_categories"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name


class Material(models.Model):
    """Vật liệu dùng để sản xuất sản phẩm."""

    name = models.CharField(max_length=255, unique=True)
    standard = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "materials"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ManufacturingProcess(models.Model):
    """Công đoạn gia công, ví dụ tiện CNC, phay CNC, mài, kiểm tra CMM."""

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "manufacturing_processes"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """Sản phẩm chính của website."""

    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, db_column="category_id")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    short_description = models.TextField()
    description = models.TextField()
    main_image = models.TextField()
    sku = models.CharField(max_length=120, blank=True, null=True)
    price = models.FloatField(default=0)
    thumbnail_url = models.TextField(blank=True, null=True)
    gallery_urls = models.TextField(blank=True, null=True)
    pdf_url = models.TextField(blank=True, null=True)
    video_url = models.TextField(blank=True, null=True)
    tags_text = models.TextField(blank=True, null=True)
    seo_title = models.CharField(max_length=255, blank=True, null=True)
    seo_description = models.TextField(blank=True, null=True)
    seo_keywords = models.TextField(blank=True, null=True)
    canonical_url = models.TextField(blank=True, null=True)
    og_image = models.TextField(blank=True, null=True)
    robots = models.CharField(max_length=80, default="index,follow")
    schema_json = models.TextField(blank=True, null=True)
    related_product_ids = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PUBLISHED)
    published_at = models.DateTimeField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "products"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    """Ảnh phụ của sản phẩm."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image_url = models.TextField()
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "product_images"
        ordering = ["sort_order", "id"]


class ProductSpec(models.Model):
    """Thông số kỹ thuật dạng key/value của sản phẩm."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="specs")
    spec_name = models.CharField(max_length=255)
    spec_value = models.CharField(max_length=255)
    unit = models.CharField(max_length=80, blank=True, null=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "product_specs"
        ordering = ["sort_order", "id"]


class ProductMaterial(models.Model):
    """Bảng nối sản phẩm với vật liệu."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = "product_materials"
        unique_together = ("product", "material")


class ProductProcess(models.Model):
    """Bảng nối sản phẩm với công đoạn gia công."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    process = models.ForeignKey(ManufacturingProcess, on_delete=models.CASCADE, db_column="process_id")
    step_order = models.IntegerField(default=0)
    note = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "product_processes"
        unique_together = ("product", "process")
        ordering = ["step_order"]
