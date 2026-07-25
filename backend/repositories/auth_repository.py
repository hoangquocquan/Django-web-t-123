from database.connection import execute_write, query_all, query_one


def get_admin_by_email_any_status(email):
    """Tìm admin theo email, kể cả tài khoản đang bị khóa."""
    return query_one(
        """
        SELECT id, full_name, email, password_hash, role, is_active, two_factor_enabled
        FROM admin_users
        WHERE email = ?
        """,
        (email,),
    )


def get_admin_by_id(admin_id):
    """Lấy thông tin admin theo id."""
    return query_one(
        """
        SELECT id, full_name, email, password_hash, role, is_active, two_factor_enabled
        FROM admin_users
        WHERE id = ?
        """,
        (admin_id,),
    )


def update_admin_password(admin_id, password_hash):
    """Cập nhật mật khẩu đã hash cho admin."""
    execute_write("UPDATE admin_users SET password_hash = ? WHERE id = ?", (password_hash, admin_id))


def update_admin_email(admin_id, email):
    """Cập nhật email đăng nhập cho admin."""
    execute_write("UPDATE admin_users SET email = ? WHERE id = ?", (email, admin_id))


def update_admin_active_status(admin_id, is_active):
    """Khóa hoặc mở khóa tài khoản admin."""
    execute_write("UPDATE admin_users SET is_active = ? WHERE id = ?", (1 if is_active else 0, admin_id))


def update_two_factor_enabled(admin_id, enabled):
    """Bật/tắt 2FA cho admin."""
    execute_write("UPDATE admin_users SET two_factor_enabled = ? WHERE id = ?", (1 if enabled else 0, admin_id))


def create_two_factor_challenge(challenge_id, admin_id, code):
    """Lưu mã 2FA tạm thời."""
    execute_write(
        """
        INSERT INTO admin_2fa_challenges (challenge_id, admin_id, code)
        VALUES (?, ?, ?)
        """,
        (challenge_id, admin_id, code),
    )


def get_two_factor_challenge(challenge_id):
    """Lấy challenge 2FA theo id."""
    return query_one(
        """
        SELECT challenge_id, admin_id, code, used_at, created_at
        FROM admin_2fa_challenges
        WHERE challenge_id = ?
        """,
        (challenge_id,),
    )


def mark_two_factor_challenge_used(challenge_id):
    """Đánh dấu mã 2FA đã dùng."""
    execute_write("UPDATE admin_2fa_challenges SET used_at = CURRENT_TIMESTAMP WHERE challenge_id = ?", (challenge_id,))


def create_password_reset_token(token, admin_id, email, expires_at):
    """Lưu token reset mật khẩu."""
    execute_write(
        """
        INSERT INTO password_reset_tokens (token, admin_id, email, expires_at)
        VALUES (?, ?, ?, ?)
        """,
        (token, admin_id, email, expires_at),
    )


def get_password_reset_token(token):
    """Lấy token reset mật khẩu."""
    return query_one(
        """
        SELECT token, admin_id, email, expires_at, used_at
        FROM password_reset_tokens
        WHERE token = ?
        """,
        (token,),
    )


def mark_password_reset_token_used(token, used_at):
    """Đánh dấu token đã dùng để không reset lại nhiều lần."""
    execute_write("UPDATE password_reset_tokens SET used_at = ? WHERE token = ?", (used_at, token))


def create_auth_email(recipient, subject, body):
    """Lưu email demo vào outbox nội bộ thay vì gửi email thật."""
    return execute_write(
        """
        INSERT INTO auth_email_outbox (recipient, subject, body)
        VALUES (?, ?, ?)
        """,
        (recipient, subject, body),
    )


def list_recent_auth_emails(limit=10):
    """Lấy danh sách email demo gần nhất."""
    return query_all(
        """
        SELECT id, recipient, subject, body, created_at
        FROM auth_email_outbox
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
