import sqlite3
from contextlib import contextmanager

from config.settings import DATABASE_PATH


def get_connection():
    """Mở kết nối SQLite và cho phép đọc dữ liệu theo tên cột."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def transaction():
    """Mở transaction: lỗi thì rollback, thành công thì commit."""
    # Transaction dùng cho thao tác ghi nhiều bước.
    # Nếu bước thứ 2 bị lỗi, các bước trước đó sẽ được hủy bằng rollback.
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def rows_to_dicts(rows):
    """Đổi danh sách dòng SQLite thành danh sách dictionary."""
    return [dict(row) for row in rows]


def query_all(sql, params=()):
    """Chạy SELECT và trả về nhiều dòng dữ liệu."""
    with get_connection() as connection:
        rows = connection.execute(sql, params).fetchall()
        return rows_to_dicts(rows)


def query_one(sql, params=()):
    """Chạy SELECT và trả về một dòng dữ liệu."""
    with get_connection() as connection:
        row = connection.execute(sql, params).fetchone()
        return dict(row) if row else None


def execute_write(sql, params=()):
    """Chạy INSERT/UPDATE/DELETE và trả về id vừa tạo."""
    with get_connection() as connection:
        cursor = connection.execute(sql, params)
        connection.commit()
        return cursor.lastrowid
