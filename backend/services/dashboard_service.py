from datetime import date, timedelta

from repositories.dashboard_repository import (
    get_dashboard_counts,
    get_recent_visits,
    get_visit_rows_by_day,
    get_visit_rows_by_month,
    insert_page_visit,
)


def get_dashboard_stats():
    return {
        "counts": get_dashboard_counts(),
        "charts": {
            "7_days": build_daily_chart(7),
            "30_days": build_daily_chart(30),
            "12_months": build_monthly_chart(12),
        },
        "recent_visits": get_recent_visits(),
    }


def track_page_visit(path, remote_addr="", user_agent=""):
    """Ghi nhận lượt truy cập public site."""
    return insert_page_visit(path, remote_addr, user_agent)


def build_daily_chart(days):
    """Tạo dữ liệu biểu đồ theo ngày, tự điền ngày không có visit bằng 0."""
    rows = {item["label"]: item["total"] for item in get_visit_rows_by_day(days)}
    start = date.today() - timedelta(days=days - 1)
    chart = []
    for index in range(days):
        current_day = start + timedelta(days=index)
        label = current_day.isoformat()
        chart.append({"label": label, "total": rows.get(label, 0)})
    return chart


def build_monthly_chart(months):
    """Tạo dữ liệu biểu đồ 12 tháng gần nhất."""
    rows = {item["label"]: item["total"] for item in get_visit_rows_by_month(months)}
    today = date.today()
    month_labels = []
    year = today.year
    month = today.month
    for _ in range(months):
        month_labels.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    month_labels.reverse()
    return [{"label": label, "total": rows.get(label, 0)} for label in month_labels]
