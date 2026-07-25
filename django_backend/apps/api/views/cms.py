"""Read-only CMS API views for Phase 9.1 cutover."""

from rest_framework.decorators import api_view, permission_classes

from apps.api.permissions import ReadOnlyApiPermission
from apps.api.serializers.cms import menu_item_to_dict, page_to_dict
from apps.api.views.helpers import handle_not_found, list_ok, ok
from apps.cms.services.cms_service import CmsService


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def pages(request):
    """Return published dynamic pages through the CMS service layer."""
    service = CmsService()
    return list_ok(page_to_dict(page) for page in service.list_public_pages())


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def page_detail(request, slug):
    """Return one published dynamic page by slug."""
    service = CmsService()
    return handle_not_found(
        "CMS page",
        lambda: ok(page_to_dict(service.get_public_page(slug))),
    )


@api_view(["GET"])
@permission_classes([ReadOnlyApiPermission])
def menu(request):
    """Return nested menu items for one location, defaulting to header."""
    location = request.query_params.get("location", "header")
    service = CmsService()
    return list_ok(
        menu_item_to_dict(item)
        for item in service.list_navigation(location=location)
    )
