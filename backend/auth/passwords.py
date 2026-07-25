import hashlib
import secrets

from config.settings import PASSWORD_SALT
from database.connection import execute_write


def legacy_hash_password(password):
    """Hash cũ bằng SHA-256, chỉ giữ để tài khoản demo cũ vẫn đăng nhập được."""
    raw_value = f"{PASSWORD_SALT}:{password}".encode("utf-8")
    return hashlib.sha256(raw_value).hexdigest()


def hash_password(password):
    """Hash mật khẩu bằng PBKDF2-HMAC-SHA256."""
    iterations = 260000
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return f"pbkdf2_sha256${iterations}${salt}${password_hash}"


def verify_password(password, password_hash):
    """So sánh mật khẩu nhập vào với hash trong database."""
    if password_hash.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt, expected_hash = password_hash.split("$", 3)
            actual_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                int(iterations),
            ).hex()
            return secrets.compare_digest(actual_hash, expected_hash)
        except ValueError:
            return False

    return secrets.compare_digest(legacy_hash_password(password), password_hash)


def password_hash_needs_upgrade(password_hash):
    """Kiểm tra hash có còn dùng định dạng cũ không."""
    return not password_hash.startswith("pbkdf2_sha256$")


def upgrade_admin_password_hash(admin_id, password):
    """Nâng cấp hash cũ lên PBKDF2 sau khi người dùng đăng nhập đúng."""
    execute_write(
        "UPDATE admin_users SET password_hash = ? WHERE id = ?",
        (hash_password(password), admin_id),
    )

