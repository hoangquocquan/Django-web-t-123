"""Service layer cho Accounts/Auth.

Service này xử lý đăng nhập, session, đổi mật khẩu và reset password cho bảng
`admin_users` cũ. Đây chưa phải auth mặc định của Django, mà là lớp tương thích
với backend hiện tại.
"""

import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import AdminActivityLog, AdminSession, AdminUser, AuthEmailOutbox, LoginAttempt, PasswordResetToken

SESSION_TTL_SECONDS = int(getattr(settings, "MEC_SESSION_TTL_SECONDS", 60 * 60 * 8))
PASSWORD_SALT = getattr(settings, "MEC_PASSWORD_SALT", "mecprecision-demo-salt")


def now_timestamp():
    """Trả timestamp hiện tại dạng số nguyên."""
    return int(timezone.now().timestamp())


def legacy_hash_password(password):
    """Hash cũ SHA-256, giữ để tài khoản demo cũ vẫn đăng nhập được."""
    return hashlib.sha256(f"{PASSWORD_SALT}:{password}".encode("utf-8")).hexdigest()


def hash_password(password):
    """Hash mật khẩu bằng PBKDF2-HMAC-SHA256 giống backend cũ."""
    iterations = 260000
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), salt.encode("utf-8"), iterations).hex()
    return f"pbkdf2_sha256${iterations}${salt}${password_hash}"


def verify_password(password, password_hash):
    """So sánh mật khẩu người dùng nhập với hash trong database."""
    password = str(password or "")
    password_hash = str(password_hash or "")
    if password_hash.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt, expected_hash = password_hash.split("$", 3)
            actual_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)).hex()
            return secrets.compare_digest(actual_hash, expected_hash)
        except ValueError:
            return False
    return secrets.compare_digest(legacy_hash_password(password), password_hash)


def record_login_attempt(email, remote_addr="", success=False):
    """Ghi lại một lần thử đăng nhập."""
    return LoginAttempt.objects.create(email=email, remote_addr=remote_addr or "", success=success, created_at=now_timestamp())


def cleanup_expired_sessions():
    """Xóa session đã hết hạn."""
    AdminSession.objects.filter(expires_at__lt=now_timestamp()).delete()


def create_admin_session(admin_user, remote_addr="", user_agent="", ttl_seconds=None):
    """Tạo session admin mới và lưu vào database."""
    expires_at = now_timestamp() + int(ttl_seconds or SESSION_TTL_SECONDS)
    session = AdminSession.objects.create(
        session_id=secrets.token_urlsafe(32),
        admin=admin_user,
        full_name=admin_user.full_name,
        email=admin_user.email,
        role=admin_user.role,
        expires_at=expires_at,
        remote_addr=remote_addr or "",
        user_agent=user_agent or "",
        last_seen_at=now_timestamp(),
    )
    return session


def login_admin(email, password, remote_addr="", user_agent="", remember_login=False):
    """Đăng nhập admin bằng email/password và trả session nếu hợp lệ."""
    email = str(email or "").strip().lower()
    password = str(password or "")
    admin = AdminUser.objects.filter(email=email).first()
    if not admin or not admin.is_active or not verify_password(password, admin.password_hash):
        record_login_attempt(email, remote_addr, False)
        raise ValueError("Email hoặc mật khẩu không đúng, hoặc tài khoản đang bị khóa.")
    record_login_attempt(email, remote_addr, True)
    ttl = 60 * 60 * 24 * 30 if remember_login else SESSION_TTL_SECONDS
    session = create_admin_session(admin, remote_addr, user_agent, ttl)
    log_activity(admin, "auth.login", "admin_user", admin.id, "Đăng nhập CMS", remote_addr)
    return session


def logout_session(session_id):
    """Đăng xuất bằng cách xóa session."""
    deleted, _ = AdminSession.objects.filter(session_id=session_id).delete()
    return deleted > 0


def get_session(session_id):
    """Lấy session còn hạn và cập nhật last_seen_at."""
    cleanup_expired_sessions()
    session = AdminSession.objects.filter(session_id=session_id, expires_at__gte=now_timestamp()).select_related("admin").first()
    if session:
        session.last_seen_at = now_timestamp()
        session.save(update_fields=["last_seen_at"])
    return session


def change_password(admin_id, current_password, new_password):
    """Đổi mật khẩu cho admin đang đăng nhập."""
    admin = AdminUser.objects.get(id=admin_id)
    if not verify_password(current_password, admin.password_hash):
        raise ValueError("Mật khẩu hiện tại không đúng.")
    if len(str(new_password or "")) < 8:
        raise ValueError("Mật khẩu mới phải có ít nhất 8 ký tự.")
    admin.password_hash = hash_password(new_password)
    admin.save(update_fields=["password_hash"])
    AdminSession.objects.filter(admin=admin).delete()
    return admin


def request_password_reset(email, base_url="http://127.0.0.1:8000"):
    """Tạo token reset password và lưu email demo vào outbox."""
    admin = AdminUser.objects.filter(email=str(email or "").strip().lower(), is_active=True).first()
    if not admin:
        return ""
    token = secrets.token_urlsafe(32)
    expires_at = now_timestamp() + 60 * 30
    reset_link = f"{base_url.rstrip('/')}/accounts/reset-password?token={token}"
    PasswordResetToken.objects.create(token=token, admin=admin, email=admin.email, expires_at=expires_at)
    AuthEmailOutbox.objects.create(recipient=admin.email, subject="Reset password MecPrecision", body=f"Link reset: {reset_link}")
    return reset_link


def reset_password_with_token(token, new_password):
    """Đặt lại mật khẩu bằng token reset."""
    if len(str(new_password or "")) < 8:
        raise ValueError("Mật khẩu mới phải có ít nhất 8 ký tự.")
    record = PasswordResetToken.objects.select_related("admin").filter(token=token, used_at__isnull=True, expires_at__gte=now_timestamp()).first()
    if not record:
        raise ValueError("Token reset password không hợp lệ hoặc đã hết hạn.")
    with transaction.atomic():
        record.admin.password_hash = hash_password(new_password)
        record.admin.save(update_fields=["password_hash"])
        record.used_at = now_timestamp()
        record.save(update_fields=["used_at"])
        AdminSession.objects.filter(admin=record.admin).delete()
    return record.admin


def set_account_active(admin_id, is_active):
    """Khóa hoặc mở khóa tài khoản admin."""
    admin = AdminUser.objects.get(id=admin_id)
    admin.is_active = bool(is_active)
    admin.save(update_fields=["is_active"])
    if not admin.is_active:
        AdminSession.objects.filter(admin=admin).delete()
    return admin


def log_activity(admin_user, action, target_type="", target_id="", description="", remote_addr=""):
    """Ghi audit log cho thao tác quan trọng."""
    return AdminActivityLog.objects.create(
        admin=admin_user,
        actor_name=admin_user.full_name if admin_user else "",
        action=action,
        target_type=target_type,
        target_id=str(target_id or ""),
        description=description,
        remote_addr=remote_addr or "",
    )


def user_to_dict(admin):
    """Đổi AdminUser model thành dict để trả JSON."""
    return {
        "id": admin.id,
        "full_name": admin.full_name,
        "email": admin.email,
        "role": admin.role,
        "is_active": admin.is_active,
        "avatar_url": admin.avatar_url,
        "two_factor_enabled": admin.two_factor_enabled,
        "created_at": admin.created_at,
    }


def session_to_dict(session):
    """Đổi AdminSession thành dict để trả JSON."""
    return {
        "session_id": session.session_id,
        "admin_id": session.admin_id,
        "email": session.email,
        "role": session.role,
        "expires_at": session.expires_at,
        "remote_addr": session.remote_addr,
        "last_seen_at": session.last_seen_at,
    }
