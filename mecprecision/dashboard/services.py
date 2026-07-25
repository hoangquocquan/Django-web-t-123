"""Service layer cho Dashboard.

Dashboard chỉ đọc dữ liệu tổng hợp từ các module khác, ví dụ sản phẩm, tin tức,
liên hệ, báo giá, session và lượt truy cập.
"""

from datetime import date, timedelta

from django.db import DatabaseError
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone

from accounts.models import AdminSession
from customers.models import ContactRequest, Customer
from news.models import NewsArticle
from products.models import Product
from quotation.models import QuoteRequest

from .models import PageVisit


def safe_count(queryset):
    """Đếm queryset; nếu test chưa tạo bảng liên quan thì trả 0 thay vì lỗi."""
    try:
        return queryset.count()
    except DatabaseError:
        return 0


def get_dashboard_counts():
    """Lấy các số liệu chính trên dashboard quản trị."""
    now_ts = int(timezone.now().timestamp())
    five_minutes_ago = now_ts - 60 * 5
    return {
        "products": safe_count(Product.objects.all()),
        "news": safe_count(NewsArticle.objects.all()),
        "customers": safe_count(Customer.objects.all()),
        "quotes": safe_count(QuoteRequest.objects.all()),
        "new_contacts": safe_count(ContactRequest.objects.filter(status="new")),
        "online_users": safe_count(AdminSession.objects.filter(expires_at__gte=now_ts, last_seen_at__gte=five_minutes_ago)),
        "visits": safe_count(PageVisit.objects.all()),
    }


def track_page_visit(path, remote_addr="", user_agent=""):
    """Ghi nhận lượt truy cập public site."""
    return PageVisit.objects.create(path=path, remote_addr=remote_addr or "", user_agent=user_agent or "")


def build_daily_chart(days):
    """Tạo dữ liệu biểu đồ theo ngày, tự điền ngày không có visit bằng 0."""
    start_day = date.today() - timedelta(days=days - 1)
    try:
        rows = (
            PageVisit.objects.filter(visited_at__date__gte=start_day)
            .annotate(label=TruncDate("visited_at"))
            .values("label")
            .annotate(total=Count("id"))
            .order_by("label")
        )
        row_map = {item["label"].isoformat(): item["total"] for item in rows}
    except DatabaseError:
        row_map = {}
    return [
        {"label": (start_day + timedelta(days=index)).isoformat(), "total": row_map.get((start_day + timedelta(days=index)).isoformat(), 0)}
        for index in range(days)
    ]


def build_monthly_chart(months):
    """Tạo dữ liệu biểu đồ 12 tháng gần nhất."""
    today = date.today()
    labels = []
    year = today.year
    month = today.month
    for _ in range(months):
        labels.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    labels.reverse()
    try:
        rows = (
            PageVisit.objects.annotate(label=TruncMonth("visited_at"))
            .values("label")
            .annotate(total=Count("id"))
            .order_by("label")
        )
        row_map = {item["label"].strftime("%Y-%m"): item["total"] for item in rows}
    except DatabaseError:
        row_map = {}
    return [{"label": label, "total": row_map.get(label, 0)} for label in labels]


def get_recent_visits(limit=8):
    """Lấy các lượt truy cập gần nhất."""
    try:
        return list(PageVisit.objects.order_by("-id")[: int(limit or 8)])
    except DatabaseError:
        return []


def get_dashboard_stats():
    """Gom toàn bộ dữ liệu dashboard thành một dict."""
    return {
        "counts": get_dashboard_counts(),
        "charts": {
            "7_days": build_daily_chart(7),
            "30_days": build_daily_chart(30),
            "12_months": build_monthly_chart(12),
        },
        "recent_visits": get_recent_visits(),
    }
