"""Managed Django models for product, customer, and inventory ownership."""

from django.db import models


DATA_CONTRACT_CHOICES = [
    ("LEGACY", "Legacy"),
    ("MVP_V1", "MVP V1"),
]
UNIT_CHOICES = [
    ("PCS", "Pieces"),
    ("KG", "Kilograms"),
    ("M", "Metres"),
    ("MM", "Millimetres"),
]
NUMBER_NAMESPACE_CHOICES = [
    ("CUS", "Customer"),
    ("PART", "Part"),
    ("MAT", "Material"),
    ("RFQ", "RFQ"),
    ("QT", "Quotation family"),
    ("SO", "Sales order"),
]


class BusinessNumberSequence(models.Model):
    """Locked counter used to allocate concurrency-safe business numbers."""

    namespace = models.CharField(max_length=16, choices=NUMBER_NAMESPACE_CHOICES)
    period = models.CharField(max_length=16)
    last_value = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "business_number_sequences"
        ordering = ["namespace", "period"]
        constraints = [
            models.UniqueConstraint(
                fields=["namespace", "period"],
                name="uq_numseq_namespace_period",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    namespace__in=["CUS", "PART", "MAT", "RFQ", "QT", "SO"]
                ),
                name="ck_numseq_namespace",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(namespace__in=["CUS", "PART", "MAT"], period="GLOBAL")
                    | models.Q(
                        namespace__in=["RFQ", "QT", "SO"],
                        period__regex=r"^[0-9]{4}$",
                    )
                ),
                name="ck_numseq_period",
            ),
            models.CheckConstraint(
                condition=models.Q(last_value__gte=0),
                name="ck_numseq_nonnegative",
            ),
        ]

    def __str__(self):
        """Return the counter namespace and period."""
        return f"{self.namespace}:{self.period}={self.last_value}"


class BusinessMaterial(models.Model):
    """Django-owned material master for MVP business records."""

    data_contract = models.CharField(
        max_length=16,
        choices=DATA_CONTRACT_CHOICES,
        default="MVP_V1",
        db_index=True,
    )
    legacy_material_id = models.IntegerField(blank=True, null=True)
    material_code = models.CharField(max_length=32)
    name = models.CharField(max_length=160)
    standard = models.CharField(max_length=120, blank=True)
    grade = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.PROTECT,
        related_name="created_business_materials",
    )
    updated_by = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.PROTECT,
        related_name="updated_business_materials",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "business_materials"
        ordering = ["material_code"]
        indexes = [
            models.Index(
                fields=["is_active", "name"],
                name="business_material_active_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["material_code"],
                name="uq_material_code",
            ),
            models.UniqueConstraint(
                fields=["legacy_material_id"],
                condition=models.Q(legacy_material_id__isnull=False),
                name="uq_material_legacy_id",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | (
                        ~models.Q(material_code="")
                        & ~models.Q(name="")
                        & models.Q(created_by__isnull=False)
                    )
                ),
                name="ck_material_v1_required",
            ),
        ]

    def __str__(self):
        """Return material code and name."""
        return f"{self.material_code} - {self.name}"


class BusinessProduct(models.Model):
    """Django-owned product record copied gradually from legacy catalog data."""

    legacy_product_id = models.IntegerField(blank=True, null=True, unique=True)
    data_contract = models.CharField(
        max_length=16,
        choices=DATA_CONTRACT_CHOICES,
        default="LEGACY",
        db_index=True,
    )
    part_code = models.CharField(max_length=32, blank=True, null=True)
    revision = models.CharField(max_length=32, blank=True, null=True)
    unit = models.CharField(
        max_length=8,
        choices=UNIT_CHOICES,
        blank=True,
        null=True,
    )
    default_material = models.ForeignKey(
        BusinessMaterial,
        on_delete=models.PROTECT,
        related_name="default_parts",
        blank=True,
        null=True,
    )
    tolerance = models.CharField(max_length=120, blank=True)
    technical_requirements = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.PROTECT,
        related_name="created_business_products",
        blank=True,
        null=True,
    )
    updated_by = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.PROTECT,
        related_name="updated_business_products",
        blank=True,
        null=True,
    )
    archived_at = models.DateTimeField(blank=True, null=True)
    legacy_category_id = models.IntegerField(blank=True, null=True)
    category_name = models.CharField(max_length=160, blank=True)
    name = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True)
    sku = models.CharField(max_length=120, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=30, default="draft")
    short_description = models.TextField(blank=True)
    description = models.TextField(blank=True)
    main_image = models.TextField(blank=True)
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True)
    seo_keywords = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)
    published_at = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "business_products"
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(fields=["status"], name="business_product_status_idx"),
            models.Index(fields=["legacy_category_id"], name="business_product_cat_idx"),
            models.Index(
                fields=["is_active", "part_code"],
                name="business_part_active_code_idx",
            ),
            models.Index(
                fields=["default_material"],
                name="business_part_material_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["part_code"],
                condition=models.Q(part_code__isnull=False),
                name="uq_part_code_nonnull",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | (
                        models.Q(part_code__isnull=False)
                        & ~models.Q(part_code="")
                        & models.Q(revision__isnull=False)
                        & ~models.Q(revision="")
                        & models.Q(unit__isnull=False)
                        & ~models.Q(name="")
                        & models.Q(created_by__isnull=False)
                    )
                ),
                name="ck_part_v1_required",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | models.Q(unit__in=["PCS", "KG", "M", "MM"])
                ),
                name="ck_part_v1_unit",
            ),
        ]

    def __str__(self):
        """Return product name for admin/debug output."""
        return self.name


class BusinessCustomer(models.Model):
    """Django-owned customer record copied gradually from legacy CRM data."""

    legacy_customer_id = models.IntegerField(blank=True, null=True, unique=True)
    data_contract = models.CharField(
        max_length=16,
        choices=DATA_CONTRACT_CHOICES,
        default="LEGACY",
        db_index=True,
    )
    customer_code = models.CharField(max_length=32, blank=True, null=True)
    company_name = models.CharField(max_length=220, blank=True)
    contact_name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=80, blank=True)
    country = models.CharField(max_length=120, default="Vietnam", blank=True)
    status = models.CharField(max_length=40, default="active")
    notes = models.TextField(blank=True)
    archived_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.PROTECT,
        related_name="created_business_customers",
        blank=True,
        null=True,
    )
    updated_by = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.PROTECT,
        related_name="updated_business_customers",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "business_customers"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["email"], name="business_customer_email_idx"),
            models.Index(fields=["status"], name="business_customer_status_idx"),
            models.Index(
                fields=["status", "company_name"],
                name="biz_customer_state_name_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["customer_code"],
                condition=models.Q(customer_code__isnull=False),
                name="uq_customer_code_nonnull",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | models.Q(status__in=["ACTIVE", "INACTIVE"])
                ),
                name="ck_customer_v1_status",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | (
                        models.Q(customer_code__isnull=False)
                        & ~models.Q(customer_code="")
                        & ~models.Q(company_name="")
                        & models.Q(created_by__isnull=False)
                    )
                ),
                name="ck_customer_v1_required",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1", status="ACTIVE")
                    | ~models.Q(email="")
                    | ~models.Q(phone="")
                ),
                name="ck_customer_v1_contact",
            ),
        ]

    def __str__(self):
        """Return the most useful customer display name."""
        return self.company_name or self.contact_name


class InventoryWarehouse(models.Model):
    """Django-owned warehouse or stock location."""

    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=160)
    location = models.CharField(max_length=220, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inventory_warehouses"
        ordering = ["code"]

    def __str__(self):
        """Return warehouse code and name."""
        return f"{self.code} - {self.name}"


class InventoryItem(models.Model):
    """Django-owned stock balance for one product in one warehouse."""

    product = models.ForeignKey(
        BusinessProduct,
        on_delete=models.PROTECT,
        related_name="inventory_items",
    )
    warehouse = models.ForeignKey(
        InventoryWarehouse,
        on_delete=models.PROTECT,
        related_name="items",
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reserved_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_point = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_items"
        unique_together = [("product", "warehouse")]
        ordering = ["product_id", "warehouse_id"]
        indexes = [
            models.Index(fields=["product", "warehouse"], name="inventory_item_product_wh_idx"),
        ]

    def __str__(self):
        """Return a compact stock balance label."""
        return f"{self.product_id}@{self.warehouse.code}: {self.quantity}"


class InventoryTransaction(models.Model):
    """Append-only inventory movement used to audit stock changes."""

    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    transaction_type = models.CharField(max_length=40)
    quantity_delta = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField(blank=True)
    reference = models.CharField(max_length=120, blank=True)
    created_by = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inventory_transactions"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["transaction_type"], name="inventory_tx_type_idx"),
        ]

    def __str__(self):
        """Return transaction type and quantity."""
        return f"{self.transaction_type}: {self.quantity_delta}"
