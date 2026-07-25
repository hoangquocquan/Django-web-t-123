"""Views Django cho module Dashboard."""

from django.http import JsonResponse
from django.shortcuts import render

from .services import get_dashboard_stats, track_page_visit


def dashboard_home(request):
    """Trang dashboard demo bằng Django template."""
    return render(request, "dashboard/dashboard_home.html", {"dashboard": get_dashboard_stats()})


def dashboard_api(request):
    """API JSON trả toàn bộ số liệu dashboard."""
    return JsonResponse(get_dashboard_stats())


def track_visit_api(request):
    """API demo ghi nhận lượt truy cập."""
    path = request.GET.get("path", "/")
    visit = track_page_visit(path, request.META.get("REMOTE_ADDR", ""), request.META.get("HTTP_USER_AGENT", ""))
    return JsonResponse({"id": visit.id, "path": visit.path, "message": "Đã ghi nhận lượt truy cập."})
