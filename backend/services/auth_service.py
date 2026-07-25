import secrets

from auth.passwords import hash_password, verify_password
from auth.sessions import delete_admin_sessions_for_user, now_timestamp
from repositories import auth_repository
from services.settings_service import get_system_settings
from services.security_service import validate_password_policy


PASSWORD_RESET_TTL_SECONDS = 60 * 30


def request_password_reset(email, base_url):
    """Tạo token quên mật khẩu và lưu email demo vào outbox."""
    normalized_email = str(email or "").strip().lower()
    if not normalized_email:
        raise ValueError("Vui lòng nhập email.")

    admin = auth_repository.get_admin_by_email_any_status(normalized_email)
    if not admin or not admin["is_active"]:
        # Thông báo chung để tránh lộ email nào tồn tại trong hệ thống.
        return None

    token = secrets.token_urlsafe(32)
    expires_at = now_timestamp() + PASSWORD_RESET_TTL_SECONDS
    reset_link = f"{base_url}/admin/reset-password?token={token}"
    auth_repository.create_password_reset_token(token, admin["id"], admin["email"], expires_at)
    auth_repository.create_auth_email(
        admin["email"],
        "Reset mật khẩu MecPrecision",
        f"Bạn có thể đặt lại mật khẩu bằng link sau trong 30 phút: {reset_link}",
    )
    return reset_link


def reset_password_with_token(token, new_password):
    """Đổi mật khẩu bằng token nhận qua email demo."""
    token = str(token or "").strip()
    new_password = str(new_password or "").strip()
    if not token:
        raise ValueError("Token reset mật khẩu không hợp lệ.")
    validate_password_policy(new_password, get_system_settings())

    record = auth_repository.get_password_reset_token(token)
    if not record or record["used_at"]:
        raise ValueError("Token reset mật khẩu không hợp lệ hoặc đã được dùng.")
    if record["expires_at"] < now_timestamp():
        raise ValueError("Token reset mật khẩu đã hết hạn.")

    auth_repository.update_admin_password(record["admin_id"], hash_password(new_password))
    auth_repository.mark_password_reset_token_used(token, now_timestamp())
    delete_admin_sessions_for_user(record["admin_id"])
    return True


def change_password(admin_id, current_password, new_password):
    """Đổi mật khẩu khi người dùng đang đăng nhập."""
    admin = auth_repository.get_admin_by_id(admin_id)
    if not admin:
        raise ValueError("Không tìm thấy tài khoản.")
    if not verify_password(str(current_password or ""), admin["password_hash"]):
        raise ValueError("Mật khẩu hiện tại không đúng.")
    validate_password_policy(new_password, get_system_settings())

    auth_repository.update_admin_password(admin_id, hash_password(str(new_password).strip()))
    delete_admin_sessions_for_user(admin_id)
    return True


def change_email(admin_id, password, new_email):
    """Đổi email đăng nhập khi người dùng xác nhận bằng mật khẩu."""
    admin = auth_repository.get_admin_by_id(admin_id)
    email = str(new_email or "").strip().lower()
    if not admin:
        raise ValueError("Không tìm thấy tài khoản.")
    if not verify_password(str(password or ""), admin["password_hash"]):
        raise ValueError("Mật khẩu xác nhận không đúng.")
    if "@" not in email:
        raise ValueError("Email mới không hợp lệ.")
    auth_repository.update_admin_email(admin_id, email)
    delete_admin_sessions_for_user(admin_id)
    return True


def set_account_active(admin_id, is_active):
    """Khóa hoặc mở khóa tài khoản."""
    auth_repository.update_admin_active_status(admin_id, is_active)
    if not is_active:
        delete_admin_sessions_for_user(admin_id)
    return auth_repository.get_admin_by_id(admin_id)


def list_auth_email_outbox(limit=10):
    """Lấy email demo gần nhất để người học kiểm tra link reset."""
    return auth_repository.list_recent_auth_emails(limit)
