"""Read-only CRM API views for Phase 9.1 cutover."""

from rest_framework.decorators import api_view, permission_classes

from apps.api.permissions import ReadOnlyApiPermission
from apps.api.serializers.crm import (
    contact_request_to_dict,
    customer_detail_to_dict,
    customer_to_dict,
)
from apps.api.views.helpers import handle_not_found, ok, paginated_ok
from apps.crm.services.crm_service import CrmService


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def customers(request):
    """Return customer profiles through the CRM service layer."""
    service = CrmService()
    return paginated_ok(request, service.list_customer_profiles(), customer_to_dict)


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def customer_detail(request, customer_id):
    """Return one customer with notes through the CRM service layer."""
    service = CrmService()
    return handle_not_found(
        "Customer",
        lambda: ok(customer_detail_to_dict(service.get_customer_profile(customer_id))),
    )


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def contact_requests(request):
    """Return public contact requests without changing read/status fields."""
    service = CrmService()
    return paginated_ok(request, service.list_contact_requests(), contact_request_to_dict)
