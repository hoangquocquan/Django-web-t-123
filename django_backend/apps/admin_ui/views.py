"""Browser-facing Django admin UI views.

Wave 6 moves the admin screen layer to Django. The views below are intentionally
thin: they handle browser forms, authentication, permissions, and rendering,
then delegate business writes to Django-owned services.
"""

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.shortcuts import redirect, render

from apps.business_core.models import BusinessCustomer, BusinessProduct, InventoryItem, InventoryWarehouse
from apps.business_core.services import BusinessCustomerService, BusinessProductService, InventoryService
from apps.foundation.models import FoundationRole
from apps.foundation.services import FoundationAuthService, FoundationPermissionService
from apps.transaction_domain.models import TransactionHistory, TransactionOrder, WorkflowApproval
from apps.transaction_domain.services import OrderService, TransactionHistoryService, WorkflowService

from .forms import (
    AdminLoginForm,
    CustomerForm,
    InventoryAdjustmentForm,
    InventoryItemForm,
    OrderCreateForm,
    OrderUpdateForm,
    ProductCreateForm,
    ProductUpdateForm,
    WarehouseForm,
    WorkflowTransitionForm,
)


ADMIN_TOKEN_SESSION_KEY = "foundation_admin_token"
ADMIN_UI_NAVIGATION = [
    {"module": "dashboard", "label": "Dashboard", "path": "/admin/"},
    {"module": "products", "label": "Products", "path": "/admin/products/"},
    {"module": "customers", "label": "Customers", "path": "/admin/customers/"},
    {"module": "inventory", "label": "Inventory", "path": "/admin/inventory/"},
    {"module": "orders", "label": "Orders", "path": "/admin/orders/"},
    {"module": "workflows", "label": "Workflows", "path": "/admin/workflows/"},
    {"module": "transactions", "label": "Transactions", "path": "/admin/transactions/"},
]


def _login_redirect():
    """Redirect unauthenticated browsers to the Django-owned admin login page."""
    return redirect("admin_ui:login")


def _current_user(request):
    """Resolve the Foundation user stored in the Django browser session."""
    raw_token = request.session.get(ADMIN_TOKEN_SESSION_KEY, "")
    if not raw_token:
        raise PermissionDenied("Admin login is required.")
    try:
        return FoundationAuthService().authenticate_token(raw_token)
    except PermissionDenied:
        request.session.pop(ADMIN_TOKEN_SESSION_KEY, None)
        raise


def _navigation_for(user):
    """Return menu items visible to the current admin user."""
    permission_service = FoundationPermissionService()
    items = []
    for item in ADMIN_UI_NAVIGATION:
        if permission_service.has_permission(user, item["module"], "read"):
            items.append(item)
    return items


def _admin_context(request, active_module, extra=None):
    """Build shared context for every migrated admin page."""
    user = _current_user(request)
    FoundationPermissionService().require_permission(user, active_module, "read")
    context = {
        "admin_user": user,
        "active_module": active_module,
        "navigation": _navigation_for(user),
        "ownership": "django",
    }
    context.update(extra or {})
    return context


def _require_write(request, module):
    """Require write permission before processing a browser form."""
    user = _current_user(request)
    FoundationPermissionService().require_permission(user, module, "write")
    return user


def _render_or_login(request, template_name, active_module, context=None):
    """Render a protected page or redirect to login when the session expired."""
    try:
        return render(request, template_name, _admin_context(request, active_module, context))
    except PermissionDenied:
        return _login_redirect()


def _form_error_message(form):
    """Convert form errors into a compact message for non-technical operators."""
    return "Please check the highlighted fields: " + "; ".join(form.errors)


def _cleaned_without_none(form):
    """Return form data without blank optional values that would override model defaults."""
    return {key: value for key, value in form.cleaned_data.items() if value is not None}


def login_view(request):
    """Authenticate an admin browser session using FoundationAuthService."""
    if request.method == "POST":
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            try:
                raw_token, _token = FoundationAuthService().login(
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password"],
                    remote_addr=request.META.get("REMOTE_ADDR", ""),
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                )
            except PermissionDenied:
                messages.error(request, "Invalid admin credentials.")
            else:
                request.session[ADMIN_TOKEN_SESSION_KEY] = raw_token
                messages.success(request, "Admin session started.")
                return redirect("admin_ui:dashboard")
        else:
            messages.error(request, _form_error_message(form))
    else:
        form = AdminLoginForm()

    return render(request, "admin_ui/login.html", {"form": form})


def logout_view(request):
    """Revoke the current Foundation token and clear the browser session."""
    raw_token = request.session.pop(ADMIN_TOKEN_SESSION_KEY, "")
    if raw_token:
        FoundationAuthService().logout(raw_token)
    messages.success(request, "Admin session ended.")
    return redirect("admin_ui:login")


def dashboard(request):
    """Render Django-owned admin dashboard counters."""
    metrics = {
        "products": BusinessProduct.objects.count(),
        "customers": BusinessCustomer.objects.count(),
        "inventory_items": InventoryItem.objects.count(),
        "orders": TransactionOrder.objects.count(),
        "workflow_approvals": WorkflowApproval.objects.count(),
        "transaction_history": TransactionHistory.objects.count(),
        "roles": FoundationRole.objects.count(),
    }
    return _render_or_login(request, "admin_ui/dashboard.html", "dashboard", {"metrics": metrics})


def products(request):
    """Render product list and create product form."""
    form = ProductCreateForm(request.POST or None)
    if request.method == "POST":
        try:
            _require_write(request, "products")
            if form.is_valid():
                BusinessProductService().create_product(**_cleaned_without_none(form))
                messages.success(request, "Product created by Django admin UI.")
                return redirect("admin_ui:products")
            messages.error(request, _form_error_message(form))
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, str(exc))

    context = {
        "form": form,
        "products": BusinessProductService().list_products(),
    }
    return _render_or_login(request, "admin_ui/products.html", "products", context)


def product_detail(request, product_id):
    """Render and update one product."""
    try:
        product = BusinessProductService().get_product(product_id)
    except ObjectDoesNotExist:
        messages.error(request, "Product not found.")
        return redirect("admin_ui:products")

    initial = {
        "name": product.name,
        "slug": product.slug,
        "sku": product.sku,
        "category_name": product.category_name,
        "price": product.price,
        "status": product.status,
        "short_description": product.short_description,
        "description": product.description,
        "main_image": product.main_image,
        "seo_title": product.seo_title,
        "seo_description": product.seo_description,
        "seo_keywords": product.seo_keywords,
        "sort_order": product.sort_order,
    }
    form = ProductUpdateForm(request.POST or None, initial=initial)
    if request.method == "POST":
        try:
            _require_write(request, "products")
            if form.is_valid():
                update_fields = {key: value for key, value in _cleaned_without_none(form).items() if key != "slug"}
                BusinessProductService().update_product(product, **update_fields)
                messages.success(request, "Product updated by Django admin UI.")
                return redirect("admin_ui:product-detail", product_id=product.id)
            messages.error(request, _form_error_message(form))
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, str(exc))

    return _render_or_login(
        request,
        "admin_ui/product_detail.html",
        "products",
        {"form": form, "product": product},
    )


def customers(request):
    """Render customer list and create customer form."""
    form = CustomerForm(request.POST or None)
    if request.method == "POST":
        try:
            _require_write(request, "customers")
            if form.is_valid():
                BusinessCustomerService().create_customer(**form.cleaned_data)
                messages.success(request, "Customer created by Django admin UI.")
                return redirect("admin_ui:customers")
            messages.error(request, _form_error_message(form))
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, str(exc))

    return _render_or_login(
        request,
        "admin_ui/customers.html",
        "customers",
        {"form": form, "customers": BusinessCustomerService().list_customers()},
    )


def customer_detail(request, customer_id):
    """Render and update one customer."""
    try:
        customer = BusinessCustomerService().get_customer(customer_id)
    except ObjectDoesNotExist:
        messages.error(request, "Customer not found.")
        return redirect("admin_ui:customers")

    initial = {
        "company_name": customer.company_name,
        "contact_name": customer.contact_name,
        "email": customer.email,
        "phone": customer.phone,
        "country": customer.country,
        "status": customer.status,
        "notes": customer.notes,
    }
    form = CustomerForm(request.POST or None, initial=initial)
    if request.method == "POST":
        try:
            _require_write(request, "customers")
            if form.is_valid():
                BusinessCustomerService().update_customer(customer, **form.cleaned_data)
                messages.success(request, "Customer updated by Django admin UI.")
                return redirect("admin_ui:customer-detail", customer_id=customer.id)
            messages.error(request, _form_error_message(form))
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, str(exc))

    return _render_or_login(
        request,
        "admin_ui/customer_detail.html",
        "customers",
        {"form": form, "customer": customer},
    )


def inventory(request):
    """Render inventory warehouses, stock balances, and creation forms."""
    warehouse_form = WarehouseForm(prefix="warehouse")
    item_form = InventoryItemForm(prefix="item")
    if request.method == "POST":
        try:
            _require_write(request, "inventory")
            if request.POST.get("form_name") == "warehouse":
                warehouse_form = WarehouseForm(request.POST, prefix="warehouse")
                if warehouse_form.is_valid():
                    InventoryService().create_warehouse(**warehouse_form.cleaned_data)
                    messages.success(request, "Warehouse created.")
                    return redirect("admin_ui:inventory")
                messages.error(request, _form_error_message(warehouse_form))
            if request.POST.get("form_name") == "item":
                item_form = InventoryItemForm(request.POST, prefix="item")
                if item_form.is_valid():
                    InventoryService().create_item(
                        product=item_form.cleaned_data["product"],
                        warehouse=item_form.cleaned_data["warehouse"],
                        quantity=item_form.cleaned_data.get("quantity") or 0,
                        reorder_point=item_form.cleaned_data.get("reorder_point") or 0,
                    )
                    messages.success(request, "Inventory item created.")
                    return redirect("admin_ui:inventory")
                messages.error(request, _form_error_message(item_form))
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, str(exc))

    context = {
        "warehouse_form": warehouse_form,
        "item_form": item_form,
        "warehouses": InventoryService().list_warehouses(),
        "items": InventoryService().list_items(),
    }
    return _render_or_login(request, "admin_ui/inventory.html", "inventory", context)


def inventory_adjust(request, item_id):
    """Process a stock adjustment form."""
    if request.method != "POST":
        return redirect("admin_ui:inventory")
    try:
        user = _require_write(request, "inventory")
        form = InventoryAdjustmentForm(request.POST)
        item = InventoryService().get_item(item_id)
        if form.is_valid():
            InventoryService().adjust_stock(
                item=item,
                quantity_delta=form.cleaned_data["quantity_delta"],
                transaction_type=form.cleaned_data.get("transaction_type") or "adjustment",
                reason=form.cleaned_data.get("reason", ""),
                reference=form.cleaned_data.get("reference", ""),
                created_by=user.email,
            )
            messages.success(request, "Inventory adjusted.")
        else:
            messages.error(request, _form_error_message(form))
    except (PermissionDenied, ObjectDoesNotExist, ValidationError) as exc:
        messages.error(request, str(exc))
    return redirect("admin_ui:inventory")


def orders(request):
    """Render order list and create order form."""
    form = OrderCreateForm(request.POST or None)
    if request.method == "POST":
        try:
            user = _require_write(request, "orders")
            if form.is_valid():
                items = []
                if form.cleaned_data.get("product") or form.cleaned_data.get("inventory_item"):
                    items.append(
                        {
                            "product_id": form.cleaned_data["product"].id if form.cleaned_data.get("product") else None,
                            "inventory_item_id": (
                                form.cleaned_data["inventory_item"].id
                                if form.cleaned_data.get("inventory_item")
                                else None
                            ),
                            "quantity": form.cleaned_data.get("quantity") or 1,
                            "unit_price": form.cleaned_data.get("unit_price") or 0,
                        }
                    )
                OrderService().create_order(
                    customer_id=form.cleaned_data["customer"].id,
                    project_name=form.cleaned_data.get("project_name", ""),
                    message=form.cleaned_data.get("message", ""),
                    items=items,
                    actor=user.email,
                )
                messages.success(request, "Order created by Django admin UI.")
                return redirect("admin_ui:orders")
            messages.error(request, _form_error_message(form))
        except (PermissionDenied, ObjectDoesNotExist, ValidationError) as exc:
            messages.error(request, str(exc))

    return _render_or_login(
        request,
        "admin_ui/orders.html",
        "orders",
        {"form": form, "orders": OrderService().list_orders()},
    )


def order_detail(request, order_id):
    """Render and update one order."""
    try:
        order = OrderService().get_order(order_id)
    except ObjectDoesNotExist:
        messages.error(request, "Order not found.")
        return redirect("admin_ui:orders")

    form = OrderUpdateForm(
        request.POST or None,
        initial={
            "project_name": order.project_name,
            "message": order.message,
            "internal_note": order.internal_note,
        },
    )
    if request.method == "POST":
        try:
            user = _require_write(request, "orders")
            if form.is_valid():
                OrderService().update_order(order, **form.cleaned_data, actor=user.email)
                messages.success(request, "Order updated by Django admin UI.")
                return redirect("admin_ui:order-detail", order_id=order.id)
            messages.error(request, _form_error_message(form))
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, str(exc))

    return _render_or_login(
        request,
        "admin_ui/order_detail.html",
        "orders",
        {"form": form, "order": order},
    )


def workflows(request):
    """Render approval list and process workflow transitions."""
    form = WorkflowTransitionForm(request.POST or None)
    if request.method == "POST":
        try:
            user = _require_write(request, "workflows")
            if form.is_valid():
                WorkflowService().transition_order(
                    order=form.cleaned_data["order"],
                    target_status=form.cleaned_data["target_status"],
                    actor=user.email,
                    note=form.cleaned_data.get("note", ""),
                )
                messages.success(request, "Workflow transitioned.")
                return redirect("admin_ui:workflows")
            messages.error(request, _form_error_message(form))
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, str(exc))

    return _render_or_login(
        request,
        "admin_ui/workflows.html",
        "workflows",
        {"form": form, "approvals": WorkflowService().list_approvals(), "orders": OrderService().list_orders()},
    )


def transactions(request):
    """Render transaction history."""
    return _render_or_login(
        request,
        "admin_ui/transactions.html",
        "transactions",
        {"history_rows": TransactionHistoryService().list_history()},
    )
