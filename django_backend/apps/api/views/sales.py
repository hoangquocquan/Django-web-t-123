"""Read-only Sales quotation API views for Phase 9.1 cutover."""

from rest_framework.decorators import api_view, permission_classes

from apps.api.permissions import ReadOnlyApiPermission
from apps.api.serializers.sales import quote_detail_to_dict, quote_file_to_dict, quote_to_dict
from apps.api.views.helpers import handle_not_found, list_ok, ok
from apps.sales.services.quotation_service import QuotationService


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def quotes(request):
    """Return quote request headers through the Sales service layer."""
    service = QuotationService()
    return list_ok(quote_to_dict(quote) for quote in service.list_quotes())


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def quote_detail(request, quote_id):
    """Return one quote with items and files through the Sales service layer."""
    service = QuotationService()
    return handle_not_found(
        "Quote",
        lambda: ok(quote_detail_to_dict(service.get_quote_detail(quote_id))),
    )


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def quote_files(request, quote_id):
    """Return quote file metadata without changing physical files."""
    service = QuotationService()
    return list_ok(
        quote_file_to_dict(file_obj)
        for file_obj in service.list_quote_files(quote_id)
    )
