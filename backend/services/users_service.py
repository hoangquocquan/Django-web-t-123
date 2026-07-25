from auth.passwords import hash_password
from repositories import users_repository
from utils.text import get_page_offset, parse_bool


def is_valid_email(email):
    """Kiểm tra email ở mức đơn giản để tránh lưu email sai định dạng."""
    return "@" in email and "." in email.split("@")[-1]


def get_admin_by_email(email):
    """Lấy tài khoản admin để kiểm tra đăng nhập."""
    if not email:
        return None
    return users_repository.get_active_admin_by_email(email.strip().lower())


def get_paginated_users(q="", page=1, per_page=8):
    keyword = f"%{q.strip()}%"
    return users_repository.list_paginated_users(keyword, per_page, get_page_offset(page, per_page))


def get_user_record(user_id):
    return users_repository.get_user_record(user_id)


def normalize_user_payload(payload, require_password=False):
    full_name = str(payload.get("full_name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    role = str(payload.get("role", "viewer")).strip() or "viewer"
    is_active = parse_bool(payload.get("is_active", 1))
    password = str(payload.get("password", "")).strip()
    avatar_url = str(payload.get("avatar_url", "")).strip()

    if not full_name or not email:
        raise ValueError("Họ tên và email là bắt buộc.")
    if not is_valid_email(email):
        raise ValueError("Email không đúng định dạng.")
    if role not in {"admin", "editor", "viewer"}:
        raise ValueError("Role chỉ được là admin, editor hoặc viewer.")
    if require_password and not password:
        raise ValueError("Mật khẩu là bắt buộc khi tạo người dùng mới.")

    user = {
        "full_name": full_name,
        "email": email,
        "role": role,
        "is_active": is_active,
        "avatar_url": avatar_url,
    }
    if password:
        user["password_hash"] = hash_password(password)
    return user


def save_user(payload, user_id=None):
    if user_id:
        user = normalize_user_payload(payload)
        if "password_hash" in user:
            users_repository.update_user_with_password(user_id, user)
        else:
            users_repository.update_user_without_password(user_id, user)
        return get_user_record(user_id)

    user = normalize_user_payload(payload, require_password=True)
    new_id = users_repository.insert_user(user)
    return get_user_record(new_id)


def delete_user(user_id):
    item = get_user_record(user_id)
    if not item:
        return None
    users_repository.delete_user_record(user_id)
    return item
