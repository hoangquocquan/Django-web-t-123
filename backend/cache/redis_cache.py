import json
import socket
from urllib.parse import urlparse

from config.settings import REDIS_CACHE_ENABLED, REDIS_URL


# File này là lớp cache Redis tối giản.
# Dự án không bắt buộc phải có Redis: nếu chưa bật cấu hình hoặc Redis chưa chạy,
# các hàm sẽ trả None để website vẫn chạy bình thường bằng SQLite.


def is_cache_enabled():
    """Kiểm tra cache Redis có đang bật không."""
    # Muốn bật cache cần cả 2 điều kiện:
    # 1. MEC_REDIS_CACHE_ENABLED=true
    # 2. MEC_REDIS_URL có địa chỉ Redis.
    return bool(REDIS_CACHE_ENABLED and REDIS_URL)


def parse_redis_url():
    """Đọc host/port/db từ chuỗi redis://localhost:6379/0."""
    # urlparse giúp tách chuỗi Redis URL thành hostname, port và database index.
    parsed = urlparse(REDIS_URL)
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 6379,
        "db": int((parsed.path or "/0").strip("/") or 0),
    }


def encode_command(*parts):
    """Đóng gói command theo Redis Serialization Protocol rất cơ bản."""
    # Redis server không nhận command Python trực tiếp.
    # Nó nhận chuỗi theo giao thức RESP, ví dụ SETEX key 60 value.
    command = f"*{len(parts)}\r\n"
    for part in parts:
        value = str(part).encode("utf-8")
        command += f"${len(value)}\r\n{value.decode('utf-8')}\r\n"
    return command.encode("utf-8")


def read_response(sock):
    """Đọc response Redis đơn giản cho string/status/integer."""
    # Redis response có ký tự đầu để báo kiểu dữ liệu:
    # $ là bulk string, + là status, : là integer, - là error.
    data = sock.recv(65536)
    if not data:
        return None
    prefix = data[:1]
    if prefix == b"$":
        header, _, rest = data.partition(b"\r\n")
        length = int(header[1:])
        if length == -1:
            return None
        while len(rest) < length + 2:
            rest += sock.recv(65536)
        return rest[:length].decode("utf-8")
    if prefix in {b"+", b":"}:
        return data[1:].split(b"\r\n", 1)[0].decode("utf-8")
    if prefix == b"-":
        raise RuntimeError(data[1:].split(b"\r\n", 1)[0].decode("utf-8"))
    return None


def execute_redis_command(*parts):
    """Gửi command tới Redis, lỗi thì trả None để app vẫn chạy được."""
    if not is_cache_enabled():
        return None
    config = parse_redis_url()
    try:
        # Mở kết nối socket ngắn hạn tới Redis.
        # timeout=1 giúp website không bị treo lâu nếu Redis chưa bật.
        with socket.create_connection((config["host"], config["port"]), timeout=1) as sock:
            if config["db"]:
                # Nếu URL có database khác 0, chọn database đó trước khi đọc/ghi.
                sock.sendall(encode_command("SELECT", config["db"]))
                read_response(sock)
            sock.sendall(encode_command(*parts))
            return read_response(sock)
    except OSError:
        return None


def get_json(key):
    """Lấy JSON từ Redis cache."""
    raw = execute_redis_command("GET", key)
    if not raw:
        return None
    # Dữ liệu lưu trong Redis là chuỗi JSON, nên cần parse về dict/list Python.
    return json.loads(raw)


def set_json(key, value, ttl_seconds=60):
    """Lưu JSON vào Redis cache với thời gian sống ttl_seconds."""
    # SETEX nghĩa là set key kèm thời hạn sống, tránh cache cũ tồn tại mãi.
    payload = json.dumps(value, ensure_ascii=False)
    return execute_redis_command("SETEX", key, ttl_seconds, payload)


def delete_key(key):
    """Xóa một key trong Redis cache."""
    return execute_redis_command("DEL", key)
