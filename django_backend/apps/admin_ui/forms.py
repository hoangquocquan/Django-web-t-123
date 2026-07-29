"""Django forms used by the migrated admin UI.

These forms validate browser input before the data reaches the Django service
layer. The service layer remains the final owner of business rules and writes.
"""

from django import forms

from apps.business_core.models import BusinessCustomer, BusinessProduct, InventoryItem, InventoryWarehouse


PRODUCT_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("published", "Published"),
    ("archived", "Archived"),
]

CUSTOMER_STATUS_CHOICES = [
    ("lead", "Lead"),
    ("active", "Active"),
    ("inactive", "Inactive"),
]

ORDER_STATUS_CHOICES = [
    ("approved", "Approve"),
    ("processing", "Move to processing"),
    ("completed", "Complete"),
    ("cancelled", "Cancel"),
]


class AdminLoginForm(forms.Form):
    """Validate admin login credentials from the browser form."""

    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)


class ProductCreateForm(forms.Form):
    """Validate product creation fields."""

    name = forms.CharField(label="Name", max_length=220)
    slug = forms.SlugField(label="Slug", max_length=240)
    sku = forms.CharField(label="SKU", max_length=120, required=False)
    category_name = forms.CharField(label="Category", max_length=160, required=False)
    price = forms.DecimalField(label="Price", max_digits=12, decimal_places=2, required=False)
    status = forms.ChoiceField(label="Status", choices=PRODUCT_STATUS_CHOICES, required=False)
    short_description = forms.CharField(label="Short description", required=False, widget=forms.Textarea)
    description = forms.CharField(label="Description", required=False, widget=forms.Textarea)
    main_image = forms.CharField(label="Main image URL", required=False)
    seo_title = forms.CharField(label="SEO title", max_length=255, required=False)
    seo_description = forms.CharField(label="SEO description", required=False, widget=forms.Textarea)
    seo_keywords = forms.CharField(label="SEO keywords", required=False)
    sort_order = forms.IntegerField(label="Sort order", required=False)


class ProductUpdateForm(ProductCreateForm):
    """Validate product update fields.

    Slug is intentionally not editable here because the current service layer
    keeps product slug stable after creation.
    """

    slug = forms.SlugField(label="Slug", max_length=240, required=False, disabled=True)


class CustomerForm(forms.Form):
    """Validate customer create/update fields."""

    company_name = forms.CharField(label="Company", max_length=220, required=False)
    contact_name = forms.CharField(label="Contact name", max_length=160)
    email = forms.EmailField(label="Email", required=False)
    phone = forms.CharField(label="Phone", max_length=80, required=False)
    country = forms.CharField(label="Country", max_length=120, required=False)
    status = forms.ChoiceField(label="Status", choices=CUSTOMER_STATUS_CHOICES, required=False)
    notes = forms.CharField(label="Notes", required=False, widget=forms.Textarea)


class WarehouseForm(forms.Form):
    """Validate warehouse creation fields."""

    code = forms.CharField(label="Code", max_length=40)
    name = forms.CharField(label="Name", max_length=160)
    location = forms.CharField(label="Location", max_length=220, required=False)
    is_active = forms.BooleanField(label="Active", required=False, initial=True)


class InventoryItemForm(forms.Form):
    """Validate inventory item creation fields."""

    product = forms.ModelChoiceField(label="Product", queryset=BusinessProduct.objects.none())
    warehouse = forms.ModelChoiceField(label="Warehouse", queryset=InventoryWarehouse.objects.none())
    quantity = forms.DecimalField(label="Quantity", max_digits=12, decimal_places=2, required=False)
    reorder_point = forms.DecimalField(label="Reorder point", max_digits=12, decimal_places=2, required=False)

    def __init__(self, *args, **kwargs):
        """Load choices lazily so tests can create data before rendering."""
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = BusinessProduct.objects.all()
        self.fields["warehouse"].queryset = InventoryWarehouse.objects.all()


class InventoryAdjustmentForm(forms.Form):
    """Validate inventory stock adjustment fields."""

    quantity_delta = forms.DecimalField(label="Quantity delta", max_digits=12, decimal_places=2)
    transaction_type = forms.ChoiceField(
        label="Type",
        choices=[
            ("adjustment", "Adjustment"),
            ("receipt", "Receipt"),
            ("issue", "Issue"),
            ("reserve", "Reserve"),
            ("release", "Release"),
        ],
        required=False,
    )
    reason = forms.CharField(label="Reason", required=False, widget=forms.Textarea)
    reference = forms.CharField(label="Reference", max_length=120, required=False)


class OrderCreateForm(forms.Form):
    """Validate a compact order creation form."""

    customer = forms.ModelChoiceField(label="Customer", queryset=BusinessCustomer.objects.none())
    project_name = forms.CharField(label="Project name", max_length=220, required=False)
    message = forms.CharField(label="Message", required=False, widget=forms.Textarea)
    product = forms.ModelChoiceField(label="Product", queryset=BusinessProduct.objects.none(), required=False)
    inventory_item = forms.ModelChoiceField(label="Inventory item", queryset=InventoryItem.objects.none(), required=False)
    quantity = forms.IntegerField(label="Quantity", min_value=1, required=False, initial=1)
    unit_price = forms.DecimalField(label="Unit price", max_digits=12, decimal_places=2, required=False)

    def __init__(self, *args, **kwargs):
        """Load related choices when the form is created."""
        super().__init__(*args, **kwargs)
        self.fields["customer"].queryset = BusinessCustomer.objects.all()
        self.fields["product"].queryset = BusinessProduct.objects.all()
        self.fields["inventory_item"].queryset = InventoryItem.objects.select_related("product", "warehouse")


class OrderUpdateForm(forms.Form):
    """Validate editable order metadata."""

    project_name = forms.CharField(label="Project name", max_length=220, required=False)
    message = forms.CharField(label="Message", required=False, widget=forms.Textarea)
    internal_note = forms.CharField(label="Internal note", required=False, widget=forms.Textarea)


class WorkflowTransitionForm(forms.Form):
    """Validate workflow transition actions."""

    order = forms.ModelChoiceField(label="Order", queryset=BusinessProduct.objects.none())
    target_status = forms.ChoiceField(label="Target status", choices=ORDER_STATUS_CHOICES)
    note = forms.CharField(label="Note", required=False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        """Use transaction orders as choices without importing at module load time."""
        from apps.transaction_domain.models import TransactionOrder

        super().__init__(*args, **kwargs)
        self.fields["order"].queryset = TransactionOrder.objects.all()
