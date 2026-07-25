from database.connection import execute_write, query_all, query_one


def get_active_admin_by_email(email):
    """Tìm tài khoản admin đang hoạt động bằng email đăng nhập."""
    return query_one(
        """
        SELECT id, full_name, email, password_hash, role, avatar_url, two_factor_enabled
        FROM admin_users
        WHERE email = ? AND is_active = 1
        """,
        (email,),
    )


def list_paginated_users(keyword, per_page, offset):
    total = query_one(
        "SELECT COUNT(*) AS total FROM admin_users WHERE full_name LIKE ? OR email LIKE ? OR role LIKE ?",
        (keyword, keyword, keyword),
    )["total"]
    items = query_all(
        """
        SELECT admin_users.id, admin_users.full_name, admin_users.email, admin_users.role,
               admin_users.is_active, admin_users.avatar_url, admin_users.two_factor_enabled,
               admin_users.created_at, MAX(admin_sessions.last_seen_at) AS last_login_at
        FROM admin_users
        LEFT JOIN admin_sessions ON admin_sessions.admin_id = admin_users.id
        WHERE admin_users.full_name LIKE ? OR admin_users.email LIKE ? OR admin_users.role LIKE ?
        GROUP BY admin_users.id
        ORDER BY admin_users.id DESC
        LIMIT ? OFFSET ?
        """,
        (keyword, keyword, keyword, per_page, offset),
    )
    return items, total


def get_user_record(user_id):
    return query_one(
        "SELECT id, full_name, email, role, is_active, avatar_url, two_factor_enabled, created_at FROM admin_users WHERE id = ?",
        (user_id,),
    )


def insert_user(user):
    return execute_write(
        """
        INSERT INTO admin_users (full_name, email, password_hash, role, is_active, avatar_url)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user["full_name"], user["email"], user["password_hash"], user["role"], user["is_active"], user.get("avatar_url", "")),
    )


def update_user_with_password(user_id, user):
    execute_write(
        """
        UPDATE admin_users
        SET full_name = ?, email = ?, role = ?, is_active = ?, avatar_url = ?, password_hash = ?
        WHERE id = ?
        """,
        (user["full_name"], user["email"], user["role"], user["is_active"], user.get("avatar_url", ""), user["password_hash"], user_id),
    )


def update_user_without_password(user_id, user):
    execute_write(
        """
        UPDATE admin_users
        SET full_name = ?, email = ?, role = ?, is_active = ?, avatar_url = ?
        WHERE id = ?
        """,
        (user["full_name"], user["email"], user["role"], user["is_active"], user.get("avatar_url", ""), user_id),
    )


def delete_user_record(user_id):
    execute_write("DELETE FROM admin_users WHERE id = ?", (user_id,))
