"""Sales quotation API views for migrated read and quote replacement contracts."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from apps.api.permissions import ReadOnlyApiPermission
from apps.api.serializers.sales import quote_detail_to_dict, quote_file_to_dict, quote_to_dict
from apps.api.views.helpers import handle_not_found, ok, paginated_ok
from apps.api.views.replacement import quote_create
from apps.sales.services.quotation_service import QuotationService


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def quotes(request):
    """Return quote request headers or accept a public quote replacement intent."""
    if request.method == "POST":
        return quote_create(request)
    service = QuotationService()
    return paginated_ok(request, service.list_quotes(), quote_to_dict)


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
    return paginated_ok(request, service.list_quote_files(quote_id), quote_file_to_dict)
