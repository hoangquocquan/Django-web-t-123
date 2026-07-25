from repositories import activity_repository
from utils.text import get_page_offset


def log_admin_activity(admin_user, action, target_type="", target_id="", description="", remote_addr=""):
    """Ghi nhật ký hoạt động của admin."""
    # admin_user là session hiện tại, có admin_id/full_name/email.
    # action là hành động ngắn, ví dụ user.create, user.update, user.lock.
    if not admin_user:
        return None
    return activity_repository.insert_activity_log(
        {
            "admin_id": admin_user.get("admin_id"),
            "actor_name": admin_user.get("full_name") or admin_user.get("email", ""),
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "description": description,
            "remote_addr": remote_addr,
        }
    )


def get_paginated_activity_logs(q="", page=1, per_page=10):
    """Lấy nhật ký hoạt động có tìm kiếm/phân trang."""
    keyword = f"%{q.strip()}%"
    return activity_repository.list_paginated_activity_logs(keyword, per_page, get_page_offset(page, per_page))


def get_recent_activity_logs(limit=8):
    """Lấy nhật ký mới nhất để hiển thị ở module Users."""
    return activity_repository.list_recent_activity_logs(limit)
