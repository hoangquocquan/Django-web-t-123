from database.connection import execute_write, query_all, query_one


def insert_activity_log(log):
    """Ghi một dòng nhật ký hoạt động vào database."""
    return execute_write(
        """
        INSERT INTO admin_activity_logs (
          admin_id, actor_name, action, target_type, target_id, description, remote_addr
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            log.get("admin_id"),
            log.get("actor_name", ""),
            log["action"],
            log.get("target_type", ""),
            str(log.get("target_id", "")),
            log.get("description", ""),
            log.get("remote_addr", ""),
        ),
    )


def list_paginated_activity_logs(keyword, per_page, offset):
    """Lấy nhật ký hoạt động có tìm kiếm và phân trang."""
    total = query_one(
        """
        SELECT COUNT(*) AS total
        FROM admin_activity_logs
        WHERE actor_name LIKE ? OR action LIKE ? OR target_type LIKE ? OR description LIKE ?
        """,
        (keyword, keyword, keyword, keyword),
    )["total"]
    items = query_all(
        """
        SELECT id, admin_id, actor_name, action, target_type, target_id, description, remote_addr, created_at
        FROM admin_activity_logs
        WHERE actor_name LIKE ? OR action LIKE ? OR target_type LIKE ? OR description LIKE ?
        ORDER BY id DESC
        LIMIT ? OFFSET ?
        """,
        (keyword, keyword, keyword, keyword, per_page, offset),
    )
    return items, total


def list_recent_activity_logs(limit=10):
    """Lấy vài dòng nhật ký mới nhất để hiển thị nhanh trong Users CMS."""
    return query_all(
        """
        SELECT id, actor_name, action, target_type, target_id, description, remote_addr, created_at
        FROM admin_activity_logs
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
