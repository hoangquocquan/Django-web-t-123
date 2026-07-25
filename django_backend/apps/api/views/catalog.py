"""Read-only Catalog API views for Phase 9.1 cutover."""

from rest_framework.decorators import api_view, permission_classes

from apps.api.permissions import ReadOnlyApiPermission
from apps.api.serializers.catalog import (
    category_to_dict,
    material_to_dict,
    product_detail_to_dict,
    product_to_dict,
)
from apps.api.views.helpers import handle_not_found, ok, paginated_ok
from apps.catalog.services.catalog_service import CatalogService


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def products(request):
    """Return read-only product list through the Catalog service layer."""
    service = CatalogService()
    return paginated_ok(request, service.list_products(), product_to_dict)


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def product_detail(request, product_id):
    """Return one product detail through the Catalog service layer."""
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
