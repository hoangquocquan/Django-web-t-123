import hmac
import hashlib
import re
import secrets
from pathlib import Path

from config.settings import PASSWORD_SALT, SESSION_TTL_SECONDS
from repositories import auth_repository


REMEMBER_LOGIN_SECONDS = 60 * 60 * 24 * 30


def make_csrf_token(session_id):
    """Tạo CSRF token từ session_id để chống form giả mạo."""
    message = str(session_id or "").encode("utf-8")
    secret = PASSWORD_SALT.encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def verify_csrf_token(session_id, token):
    """Kiểm tra CSRF token gửi từ form admin có khớp session hiện tại không."""
    expected = make_csrf_token(session_id)
    return hmac.compare_digest(expected, str(token or ""))


def inject_csrf_token(html, session_id):
    """Tự động thêm input csrf_token vào mọi form trong khung Admin."""
    token = make_csrf_token(session_id)
    hidden_input = f'<input type="hidden" name="csrf_token" value="{token}" />'
    return re.sub(r"(<form\b[^>]*>)", rf"\1{hidden_input}", html)


def get_session_ttl(remember_login=False):
    """Remember Login dùng session dài hơn session bình thường."""
    return REMEMBER_LOGIN_SECONDS if remember_login else SESSION_TTL_SECONDS


def make_captcha_challenge():
    """Tạo captcha cộng số đơn giản cho trang login local."""
    left = secrets.randbelow(8) + 2
    right = secrets.randbelow(8) + 2
    answer = str(left + right)
    token = hmac.new(PASSWORD_SALT.encode("utf-8"), answer.encode("utf-8"), hashlib.sha256).hexdigest()
    return {"question": f"{left} + {right} = ?", "token": token}


def verify_captcha(answer, token):
    """Kiểm tra captcha bằng chữ ký HMAC, không cần lưu session tạm."""
    expected = hmac.new(PASSWORD_SALT.encode("utf-8"), str(answer or "").strip().encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, str(token or ""))


def is_ip_allowed(remote_addr, settings):
    """Kiểm tra IP whitelist; để trống nghĩa là cho phép mọi IP."""
    whitelist = str(settings.get("ip_whitelist", "")).strip()
    if not whitelist:
        return True
    allowed_ips = {item.strip() for item in whitelist.replace("\n", ",").split(",") if item.strip()}
    return str(remote_addr or "") in allowed_ips


def validate_password_policy(password, settings):
    """Kiểm tra password policy cấu hình trong Settings."""
    password = str(password or "")
    min_length = int(settings.get("password_min_length", 8) or 8)
    if len(password) < min_length:
        raise ValueError(f"Mật khẩu cần ít nhất {min_length} ký tự.")
    if settings.get("password_require_uppercase") == "1" and not any(char.isupper() for char in password):
        raise ValueError("Mật khẩu cần ít nhất 1 chữ hoa.")
    if settings.get("password_require_digit") == "1" and not any(char.isdigit() for char in password):
        raise ValueError("Mật khẩu cần ít nhất 1 chữ số.")
    return True


def create_two_factor_challenge(admin_user):
    """Tạo mã 2FA và lưu email demo vào outbox."""
    code = f"{secrets.randbelow(1000000):06d}"
    challenge_id = secrets.token_urlsafe(24)
    auth_repository.create_two_factor_challenge(challenge_id, admin_user["id"], code)
    auth_repository.create_auth_email(
        admin_user["email"],
        "Mã 2FA MecPrecision",
        f"Mã xác thực 2FA của bạn là: {code}. Mã có hiệu lực trong vài phút.",
    )
    return challenge_id


def verify_two_factor_challenge(challenge_id, code):
    """Xác thực mã 2FA một lần."""
    challenge = auth_repository.get_two_factor_challenge(challenge_id)
    if not challenge or challenge["used_at"]:
        raise ValueError("Mã 2FA không hợp lệ hoặc đã được dùng.")
    if not hmac.compare_digest(str(challenge["code"]), str(code or "").strip()):
        raise ValueError("Mã 2FA không đúng.")
    auth_repository.mark_two_factor_challenge_used(challenge_id)
    return auth_repository.get_admin_by_id(challenge["admin_id"])


def set_two_factor_enabled(admin_id, enabled):
    """Bật hoặc tắt 2FA cho tài khoản admin."""
    auth_repository.update_two_factor_enabled(admin_id, 1 if enabled else 0)
    return auth_repository.get_admin_by_id(admin_id)
