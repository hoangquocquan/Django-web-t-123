import mimetypes
import re
import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from config.settings import UPLOAD_ROOT


ALLOWED_MEDIA_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".pdf", ".step", ".stp", ".dxf"}


def slug_filename(name):
    """Đổi tên file/thư mục về dạng an toàn để lưu trên ổ đĩa."""
    value = Path(str(name or "")).stem.strip().lower()
    value = re.sub(r"[^a-z0-9_-]+", "-", value)
    return value.strip("-") or "media"


def normalize_folder(folder):
    """Chuẩn hóa tên folder, chỉ cho phép các segment an toàn."""
    folder = str(folder or "").strip().replace("\\", "/").strip("/")
    if not folder:
        return ""
    safe_parts = [slug_filename(part) for part in folder.split("/") if part.strip()]
    return "/".join(safe_parts)


def resolve_upload_path(url_or_path):
    """Đổi URL /uploads/... thành đường dẫn thật và kiểm tra không vượt khỏi uploads."""
    raw_value = str(url_or_path or "").strip()
    relative = raw_value.replace("/uploads/", "", 1).lstrip("/") if raw_value.startswith("/uploads/") else raw_value.lstrip("/")
    target_path = (UPLOAD_ROOT / relative).resolve()
    upload_root = UPLOAD_ROOT.resolve()
    if upload_root not in target_path.parents and target_path != upload_root:
        raise ValueError("Đường dẫn media không hợp lệ.")
    return target_path


def path_to_url(path):
    """Đổi đường dẫn thật trong uploads thành URL public."""
    relative = path.resolve().relative_to(UPLOAD_ROOT.resolve()).as_posix()
    return f"/uploads/{relative}"


def ensure_upload_root():
    """Tạo thư mục uploads nếu chưa tồn tại."""
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)


def list_media(folder="", q=""):
    """Liệt kê file media, hỗ trợ folder và tìm kiếm."""
    ensure_upload_root()
    safe_folder = normalize_folder(folder)
    base_dir = resolve_upload_path(safe_folder)
    base_dir.mkdir(parents=True, exist_ok=True)
    keyword = str(q or "").strip().lower()
    items = []

    for path in base_dir.rglob("*"):
        if not path.is_file():
            continue
        if keyword and keyword not in path.name.lower() and keyword not in path_to_url(path).lower():
            continue
        stat = path.stat()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        items.append(
            {
                "name": path.name,
                "url": path_to_url(path),
                "folder": path.parent.resolve().relative_to(UPLOAD_ROOT.resolve()).as_posix(),
                "size": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "content_type": content_type,
                "is_image": content_type.startswith("image/"),
            }
        )

    return sorted(items, key=lambda item: item["modified_at"], reverse=True)


def list_folders():
    """Liệt kê folder con trong uploads."""
    ensure_upload_root()
    folders = [""]
    for path in UPLOAD_ROOT.rglob("*"):
        if path.is_dir():
            folders.append(path.resolve().relative_to(UPLOAD_ROOT.resolve()).as_posix())
    return sorted(set(folders))


def create_folder(folder):
    """Tạo folder media mới."""
    safe_folder = normalize_folder(folder)
    if not safe_folder:
        raise ValueError("Tên folder không hợp lệ.")
    target_dir = resolve_upload_path(safe_folder)
    target_dir.mkdir(parents=True, exist_ok=True)
    return safe_folder


def save_media_file(file_item, folder="images"):
    """Upload một file vào Media Manager."""
    if file_item is None or not getattr(file_item, "filename", ""):
        raise ValueError("Vui lòng chọn file upload.")
    original_name = Path(file_item.filename).name
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_MEDIA_SUFFIXES:
        raise ValueError("Định dạng file không được hỗ trợ.")

    safe_folder = normalize_folder(folder) or "images"
    target_dir = resolve_upload_path(safe_folder)
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{slug_filename(original_name)}-{uuid4().hex[:8]}{suffix}"
    target_path = target_dir / safe_name
    with target_path.open("wb") as output:
        shutil.copyfileobj(file_item.file, output)
    return path_to_url(target_path)


def rename_media(url, new_name):
    """Đổi tên file media, giữ nguyên đuôi file cũ."""
    current_path = resolve_upload_path(url)
    if not current_path.exists() or not current_path.is_file():
        raise ValueError("Không tìm thấy file media.")
    suffix = current_path.suffix.lower()
    safe_name = f"{slug_filename(new_name)}{suffix}"
    new_path = current_path.with_name(safe_name)
    if new_path.exists():
        raise ValueError("Tên file mới đã tồn tại.")
    current_path.rename(new_path)
    return path_to_url(new_path)


def delete_media(url):
    """Xóa một file media."""
    target_path = resolve_upload_path(url)
    if not target_path.exists() or not target_path.is_file():
        raise ValueError("Không tìm thấy file media.")
    target_url = path_to_url(target_path)
    target_path.unlink()
    return target_url
