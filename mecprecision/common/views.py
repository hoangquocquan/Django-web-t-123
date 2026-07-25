"""Views Django cho Common/System."""

from django.http import JsonResponse
from django.shortcuts import render

from .services import get_menu_items, get_published_pages, health_check


def common_home(request):
    """Trang demo Common/System."""
    return render(request, "common/common_home.html", {"health": health_check()})


def health_api(request):
    """API health check cho Developer/monitor."""
    return JsonResponse(health_check())


def pages_api(request):
    """API danh sách trang động đã published."""
    return JsonResponse({"results": [{"id": page.id, "title": page.title, "slug": page.slug, "status": page.status} for page in get_published_pages()]})


def menu_api(request):
    """API menu theo location."""
    location = request.GET.get("location", "header")
    return JsonResponse({"location": location, "results": [{"id": item.id, "label": item.label, "url": item.url, "parent_id": item.parent_id} for item in get_menu_items(location)]})
