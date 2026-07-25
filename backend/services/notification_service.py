from repositories import enterprise_repository


def create_notification(title, message, level="info", recipient_type="admin", recipient_id=None):
    """Tạo notification trong CMS."""
    title = str(title or "").strip()
    message = str(message or "").strip()
    if not title or not message:
        raise ValueError("Notification cần title và message.")
    return enterprise_repository.insert_notification(
        {
            "title": title,
            "message": message,
            "level": level,
            "recipient_type": recipient_type,
            "recipient_id": recipient_id,
        }
    )


def get_recent_notifications(limit=20):
    """Lấy danh sách notification gần nhất."""
    return enterprise_repository.list_recent_notifications(limit)


def mark_notification_read(notification_id):
    """Đánh dấu notification đã đọc."""
    enterprise_repository.mark_notification_read(notification_id)

