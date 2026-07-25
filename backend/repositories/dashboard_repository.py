from auth.sessions import now_timestamp
from database.connection import execute_write, query_all, query_one


def get_dashboard_counts():
    return {
        "products": query_one("SELECT COUNT(*) AS total FROM products")["total"],
        "news": query_one("SELECT COUNT(*) AS total FROM news")["total"],
        "customers": query_one("SELECT COUNT(*) AS total FROM customers")["total"],
        "quotes": query_one("SELECT COUNT(*) AS total FROM quote_requests")["total"],
        "new_contacts": query_one("SELECT COUNT(*) AS total FROM contact_requests WHERE status = 'new'")["total"],
        "online_users": query_one(
            """
            SELECT COUNT(*) AS total
            FROM admin_sessions
            WHERE expires_at >= ? AND COALESCE(last_seen_at, expires_at) >= ?
            """,
            (now_timestamp(), now_timestamp() - 60 * 5),
        )["total"],
        "visits": query_one("SELECT COUNT(*) AS total FROM page_visits")["total"],
    }


def insert_page_visit(path, remote_addr="", user_agent=""):
    """Ghi một lượt truy cập public site."""
    return execute_write(
        """
        INSERT INTO page_visits (path, remote_addr, user_agent)
        VALUES (?, ?, ?)
        """,
        (path, remote_addr or "", user_agent or ""),
    )


def get_visit_rows_by_day(days):
    """Lấy số lượt truy cập theo ngày trong N ngày gần nhất."""
    return query_all(
        """
        SELECT date(visited_at) AS label, COUNT(*) AS total
        FROM page_visits
        WHERE date(visited_at) >= date('now', ?)
        GROUP BY date(visited_at)
        ORDER BY label
        """,
        (f"-{days - 1} days",),
    )


def get_visit_rows_by_month(months):
    """Lấy số lượt truy cập theo tháng trong N tháng gần nhất."""
    return query_all(
        """
        SELECT strftime('%Y-%m', visited_at) AS label, COUNT(*) AS total
        FROM page_visits
        WHERE date(visited_at) >= date('now', ?)
        GROUP BY strftime('%Y-%m', visited_at)
        ORDER BY label
        """,
        (f"-{months - 1} months",),
    )


def get_recent_visits(limit=8):
    """Lấy một số lượt truy cập gần nhất để kiểm tra nhanh."""
    return query_all(
        """
        SELECT id, path, remote_addr, user_agent, visited_at
        FROM page_visits
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
