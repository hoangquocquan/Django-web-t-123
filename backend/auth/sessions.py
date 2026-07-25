import secrets
import time

from config.settings import (
    LOGIN_RATE_LIMIT_MAX_ATTEMPTS,
    LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    SESSION_TTL_SECONDS,
)
from database.connection import execute_write, query_all, query_one


def now_timestamp():
    """Trả về timestamp hiện tại dạng số giây."""
    return int(time.time())


def record_login_attempt(email, remote_addr, success):
    """Ghi lại lần đăng nhập để audit và chống brute force đơn giản."""
    execute_write(
        """
        INSERT INTO login_attempts (email, remote_addr, success, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (email, remote_addr or "", 1 if success else 0, now_timestamp()),
    )


def is_login_rate_limited(email, remote_addr):
    """Chặn tạm nếu đăng nhập sai quá nhiều lần trong vài phút."""
    cutoff = now_timestamp() - LOGIN_RATE_LIMIT_WINDOW_SECONDS
    row = query_one(
        """
        SELECT COUNT(*) AS total
        FROM login_attempts
        WHERE email = ? AND remote_addr = ? AND success = 0 AND created_at >= ?
        """,
        (email, remote_addr or "", cutoff),
    )
    return row["total"] >= LOGIN_RATE_LIMIT_MAX_ATTEMPTS


def create_admin_session(admin_user, remote_addr="", user_agent="", ttl_seconds=None):
    """Tạo session admin lưu trong SQLite."""
    session_id = secrets.token_urlsafe(32)
    expires_at = now_timestamp() + (ttl_seconds or SESSION_TTL_SECONDS)
    execute_write(
        """
        INSERT INTO admin_sessions (
          session_id, admin_id, full_name, email, role, expires_at, remote_addr, user_agent, last_seen_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            admin_user["id"],
            admin_user["full_name"],
            admin_user["email"],
            admin_user["role"],
            expires_at,
            remote_addr or "",
            user_agent or "",
            now_timestamp(),
        ),
    )
    return session_id


def get_admin_session(session_id):
    """Lấy session còn hạn từ SQLite."""
    if not session_id:
        return None
    session = query_one(
        """
        SELECT session_id, admin_id, full_name, email, role, expires_at, remote_addr, user_agent, last_seen_at, created_at
        FROM admin_sessions
        WHERE session_id = ?
        """,
        (session_id,),
    )
    if not session:
        return None
    if session["expires_at"] < now_timestamp():
        delete_admin_session(session_id)
        return None
    execute_write("UPDATE admin_sessions SET last_seen_at = ? WHERE session_id = ?", (now_timestamp(), session_id))
    return session


def delete_admin_session(session_id):
    """Xóa session khỏi SQLite."""
    if session_id:
        execute_write("DELETE FROM admin_sessions WHERE session_id = ?", (session_id,))


def delete_admin_session_for_user(admin_id, session_id):
    """Xóa một session nhưng chỉ khi nó thuộc đúng admin."""
    execute_write("DELETE FROM admin_sessions WHERE admin_id = ? AND session_id = ?", (admin_id, session_id))


def delete_admin_sessions_for_user(admin_id):
    """Xóa toàn bộ session của một admin, dùng khi khóa tài khoản hoặc đổi mật khẩu."""
    execute_write("DELETE FROM admin_sessions WHERE admin_id = ?", (admin_id,))


def list_admin_sessions(admin_id):
    """Lấy danh sách session còn hạn của một admin."""
    cleanup_expired_sessions()
    return query_all(
        """
        SELECT session_id, admin_id, remote_addr, user_agent, expires_at, last_seen_at, created_at
        FROM admin_sessions
        WHERE admin_id = ?
        ORDER BY last_seen_at DESC, created_at DESC
        """,
        (admin_id,),
    )


def cleanup_expired_sessions():
    """Dọn session hết hạn."""
    execute_write("DELETE FROM admin_sessions WHERE expires_at < ?", (now_timestamp(),))
