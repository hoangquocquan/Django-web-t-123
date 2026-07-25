"""Catalog API views for migrated read and replacement write contracts."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from apps.api.permissions import ReadOnlyApiPermission
from apps.api.serializers.catalog import (
    category_to_dict,
    material_to_dict,
    product_detail_to_dict,
    product_to_dict,
)
from apps.api.views.helpers import handle_not_found, ok, paginated_ok
from apps.api.views.replacement import product_create, product_write_detail
from apps.catalog.services.catalog_service import CatalogService


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def products(request):
    """Return product list or accept a protected product create replacement."""
    if request.method == "POST":
        return product_create(request)
    service = CatalogService()
    return paginated_ok(request, service.list_products(), product_to_dict)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([AllowAny])
def product_detail(request, product_id):
    """Return one product detail or accept protected write replacement intent."""
    if request.method in {"PUT", "DELETE"}:
        return product_write_detail(request, product_id)
    service = CatalogService()
    return handle_not_found(
        "Product",
        lambda: ok(product_detail_to_dict(service.get_product_detail(product_id))),
    )


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def categories(request):
    """Return read-only product categories through the Catalog service layer."""
    service = CatalogService()
    return paginated_ok(request, service.list_categories(), category_to_dict)


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def materials(request):
    """Return read-only manufacturing materials through the Catalog service."""
    service = CatalogService()
    return paginated_ok(request, service.list_materials(), material_to_dict)
