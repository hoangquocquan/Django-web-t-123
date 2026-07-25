"""Sao chép database legacy sang khu vực test.

File này chỉ phục vụ kiểm thử Django ORM đọc database cũ.
Nó không chỉnh sửa database gốc và cũng không chạy migrate.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "backend" / "database" / "mecprecision.sqlite"
DEFAULT_DESTINATION = (
    PROJECT_ROOT
    / "django_backend"
    / "tests"
    / "fixtures"
    / "legacy_database"
    / "mecprecision-test.sqlite"
)


def copy_legacy_database(source: Path = DEFAULT_SOURCE, destination: Path = DEFAULT_DESTINATION) -> Path:
    """Tạo một bản copy database để test sử dụng thay vì đụng vào database thật."""
    source = Path(source)
    destination = Path(destination)

    if not source.exists():
        raise FileNotFoundError(f"Không tìm thấy database legacy: {source}")

    if source.resolve() == destination.resolve():
        raise ValueError("Source và destination không được trỏ tới cùng một file.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def main() -> None:
    """Cho phép chạy script trực tiếp từ terminal khi cần chuẩn bị fixture."""
    parser = argparse.ArgumentParser(description="Copy legacy SQLite database for Django tests.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()

    copied_path = copy_legacy_database(args.source, args.destination)
    print(f"Đã tạo database test: {copied_path}")


if __name__ == "__main__":
    main()
