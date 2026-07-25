import json

from database.connection import execute_write, query_all, query_one


def insert_event(event):
    """Lưu event nghiệp vụ để audit/trace luồng hệ thống."""
    return execute_write(
        """
        INSERT INTO enterprise_events (event_name, entity_type, entity_id, payload, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            event["event_name"],
            event.get("entity_type", ""),
            str(event.get("entity_id", "")),
            json.dumps(event.get("payload", {}), ensure_ascii=False),
            event.get("status", "published"),
        ),
    )


def list_recent_events(limit=20):
    """Lấy event mới nhất cho Developer panel."""
    return query_all(
        """
        SELECT id, event_name, entity_type, entity_id, payload, status, created_at
        FROM enterprise_events
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )


def insert_job(job):
    """Đưa job vào hàng đợi xử lý nền."""
    return execute_write(
        """
        INSERT INTO job_queue (job_type, payload, status, available_at)
        VALUES (?, ?, 'pending', COALESCE(NULLIF(?, ''), CURRENT_TIMESTAMP))
        """,
        (job["job_type"], json.dumps(job.get("payload", {}), ensure_ascii=False), job.get("available_at", "")),
    )


def list_pending_jobs(limit=10):
    """Lấy job pending đến hạn chạy."""
    return query_all(
        """
        SELECT id, job_type, payload, status, attempts, last_error
        FROM job_queue
        WHERE status = 'pending' AND datetime(available_at) <= datetime('now')
        ORDER BY id
        LIMIT ?
        """,
        (limit,),
    )


def mark_job_running(job_id):
    """Đánh dấu job đang chạy."""
    execute_write(
        "UPDATE job_queue SET status = 'running', attempts = attempts + 1, started_at = CURRENT_TIMESTAMP WHERE id = ?",
        (job_id,),
    )


def mark_job_succeeded(job_id):
    """Đánh dấu job chạy thành công."""
    execute_write(
        "UPDATE job_queue SET status = 'succeeded', finished_at = CURRENT_TIMESTAMP, last_error = '' WHERE id = ?",
        (job_id,),
    )


def mark_job_failed(job_id, error):
    """Đánh dấu job lỗi để developer xem và xử lý."""
    execute_write(
        "UPDATE job_queue SET status = 'failed', finished_at = CURRENT_TIMESTAMP, last_error = ? WHERE id = ?",
        (str(error), job_id),
    )


def list_recent_jobs(limit=20):
    """Lấy job gần nhất cho Developer panel."""
    return query_all(
        """
        SELECT id, job_type, status, attempts, last_error, created_at, started_at, finished_at
        FROM job_queue
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )


def get_job_counts():
    """Đếm job theo trạng thái."""
    rows = query_all("SELECT status, COUNT(*) AS total FROM job_queue GROUP BY status")
    return {row["status"]: row["total"] for row in rows}


def insert_notification(notification):
    """Tạo thông báo trong CMS."""
    return execute_write(
        """
        INSERT INTO notifications (recipient_type, recipient_id, title, message, level)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            notification.get("recipient_type", "admin"),
            notification.get("recipient_id"),
            notification["title"],
            notification["message"],
            notification.get("level", "info"),
        ),
    )


def list_recent_notifications(limit=20):
    """Lấy thông báo mới nhất."""
    return query_all(
        """
        SELECT id, recipient_type, recipient_id, title, message, level, is_read, created_at, read_at
        FROM notifications
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )


def mark_notification_read(notification_id):
    """Đánh dấu thông báo đã đọc."""
    execute_write(
        "UPDATE notifications SET is_read = 1, read_at = CURRENT_TIMESTAMP WHERE id = ?",
        (notification_id,),
    )

