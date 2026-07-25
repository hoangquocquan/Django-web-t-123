"""CRM API views for migrated read and contact replacement contracts."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from apps.api.permissions import ReadOnlyApiPermission
from apps.api.serializers.crm import (
    contact_request_to_dict,
    customer_detail_to_dict,
    customer_to_dict,
)
from apps.api.views.helpers import handle_not_found, ok, paginated_ok
from apps.api.views.replacement import contact_create
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


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def contact_requests(request):
    """Return contact requests or accept a public contact replacement intent."""
    if request.method == "POST":
        return contact_create(request)
    service = CrmService()
    return paginated_ok(request, service.list_contact_requests(), contact_request_to_dict)
