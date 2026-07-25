from pathlib import Path
import shutil
from uuid import uuid4

from config.settings import UPLOAD_ROOT


def save_uploaded_file(file_item, subfolder="images"):
    """Lưu file upload vào backend/uploads và trả về URL public."""
    # FieldStorage không hỗ trợ kiểm tra kiểu `if not file_item`.
    # So sánh rõ với None để form upload avatar/sản phẩm không bị lỗi 500.
    if file_item is None or not getattr(file_item, "filename", ""):
        return ""

    original_name = Path(file_item.filename).name
    suffix = Path(original_name).suffix.lower()
    allowed_suffixes = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf", ".step", ".stp", ".dxf"}
    if suffix not in allowed_suffixes:
        raise ValueError("Định dạng file không được hỗ trợ.")

    target_dir = UPLOAD_ROOT / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{uuid4().hex}{suffix}"

    with target_path.open("wb") as output:
        shutil.copyfileobj(file_item.file, output)

    return f"/uploads/{subfolder}/{target_path.name}"
