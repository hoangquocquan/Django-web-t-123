import json

from repositories import enterprise_repository


def enqueue_job(job_type, payload=None, available_at=""):
    """Đẩy một job vào queue SQLite."""
    return enterprise_repository.insert_job(
        {
            "job_type": job_type,
            "payload": payload or {},
            "available_at": available_at,
        }
    )


def get_queue_summary():
    """Tóm tắt queue cho Developer panel."""
    return {
        "counts": enterprise_repository.get_job_counts(),
        "recent_jobs": enterprise_repository.list_recent_jobs(20),
    }


def dispatch_job(job_type, payload):
    """Chạy job theo loại."""
    # Import trong hàm để tránh vòng import giữa các service.
    if job_type == "email.send":
        from services.email_service import send_email

        return send_email(payload["recipient"], payload["subject"], payload.get("body", ""))
    if job_type == "notification.create":
        from services.notification_service import create_notification

        return create_notification(
            payload["title"],
            payload["message"],
            payload.get("level", "info"),
            payload.get("recipient_type", "admin"),
            payload.get("recipient_id"),
        )
    if job_type == "database.backup":
        from services.developer_service import create_database_backup

        return str(create_database_backup())
    raise ValueError(f"Job type chưa hỗ trợ: {job_type}")


def process_pending_jobs(limit=10):
    """Worker xử lý job pending."""
    results = []
    for job in enterprise_repository.list_pending_jobs(limit):
        payload = json.loads(job["payload"] or "{}")
        enterprise_repository.mark_job_running(job["id"])
        try:
            dispatch_job(job["job_type"], payload)
            enterprise_repository.mark_job_succeeded(job["id"])
            results.append({"id": job["id"], "status": "succeeded"})
        except Exception as error:
            enterprise_repository.mark_job_failed(job["id"], error)
            results.append({"id": job["id"], "status": "failed", "error": str(error)})
    return results

