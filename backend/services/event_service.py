from repositories import enterprise_repository
from services.queue_service import enqueue_job
from services.settings_service import get_system_settings


def publish_event(event_name, entity_type="", entity_id="", payload=None):
    """Publish event nghiệp vụ và tạo job nền liên quan."""
    payload = payload or {}
    event_id = enterprise_repository.insert_event(
        {
            "event_name": event_name,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "payload": payload,
            "status": "published",
        }
    )
    create_jobs_for_event(event_name, payload)
    return event_id


def create_jobs_for_event(event_name, payload):
    """Từ event tạo ra các job để queue xử lý sau."""
    if event_name == "contact.created":
        settings = get_system_settings()
        message = f"{payload.get('name', 'Khách hàng')} gửi liên hệ: {payload.get('contact', '')}"
        enqueue_job(
            "notification.create",
            {"title": "Liên hệ mới", "message": message, "level": "info"},
        )
        enqueue_job(
            "email.send",
            {
                "recipient": settings.get("contact_email"),
                "subject": "MecPrecision - Có liên hệ mới",
                "body": message,
            },
        )
    elif event_name == "quote.created":
        message = f"Yêu cầu báo giá mới: {payload.get('project_name', '')}"
        enqueue_job(
            "notification.create",
            {"title": "Báo giá mới", "message": message, "level": "success"},
        )
    elif event_name == "database.backup.requested":
        enqueue_job("database.backup", payload)


def get_recent_events(limit=20):
    """Lấy event gần nhất cho Developer panel."""
    return enterprise_repository.list_recent_events(limit)

