from html import escape
import re
import secrets
import unicodedata


def h(value):
    """Escape dữ liệu trước khi đưa vào HTML."""
    return escape("" if value is None else str(value), quote=True)


def make_slug(value):
    """Tạo slug URL từ tiếng Việt có dấu."""
    normalized = unicodedata.normalize("NFD", str(value).strip().lower())
    without_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    slug = re.sub(r"[^a-z0-9]+", "-", without_marks).strip("-")
    return slug or f"san-pham-{secrets.token_hex(4)}"


def parse_bool(value):
    """Đổi dữ liệu form/API thành 0 hoặc 1 để lưu SQLite."""
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int):
        return 1 if value else 0
    return 1 if str(value).strip().lower() in {"1", "true", "yes", "on"} else 0


def parse_positive_int(value, default=1):
    """Đổi giá trị query/form thành số nguyên dương."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number > 0 else default


def get_page_offset(page, per_page):
    """Tính OFFSET cho phân trang SQL."""
    return (page - 1) * per_page


def build_query_string(params):
    """Tạo query string đơn giản cho link phân trang."""
    pairs = []
    for key, value in params.items():
        if value not in (None, ""):
            pairs.append(f"{key}={h(value)}")
    return "&".join(pairs)

