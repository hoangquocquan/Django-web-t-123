import os
import platform
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from cache.redis_cache import delete_key, is_cache_enabled
from config.settings import DATABASE_PATH, ENVIRONMENT, LOG_ROOT, PROJECT_ROOT, REDIS_CACHE_ENABLED, REDIS_URL
from database.migrations import ensure_cms_tables


API_VERSION = "1.1.0"
BACKUP_ROOT = PROJECT_ROOT / "backups"


def get_health_status():
    """Health Check kiểm tra app, database và cache."""
    database_ok = Path(DATABASE_PATH).exists()
    sqlite_version = sqlite3.sqlite_version
    return {
        "status": "ok" if database_ok else "degraded",
        "api_version": API_VERSION,
        "environment": ENVIRONMENT,
        "database": "ok" if database_ok else "missing",
        "sqlite_version": sqlite_version,
        "redis_enabled": is_cache_enabled(),
    }


def get_system_info():
    """Thông tin hệ thống giúp developer/debug production."""
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cwd": str(PROJECT_ROOT),
        "environment": ENVIRONMENT,
        "database_path": str(DATABASE_PATH),
        "redis_cache_enabled": str(REDIS_CACHE_ENABLED),
        "redis_url": REDIS_URL,
    }


def clear_runtime_cache():
    """Xóa các cache runtime quan trọng."""
    # Dự án hiện mới cache api:home, sau này thêm key mới thì bổ sung tại đây.
    delete_key("api:home")
    return True


def read_recent_logs(limit=120):
    """Đọc các dòng log gần nhất từ backend/logs/app.log."""
    log_file = LOG_ROOT / "app.log"
    if not log_file.exists():
        return []
    return log_file.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]


def run_migrations():
    """Chạy migration thủ công từ Developer panel."""
    ensure_cms_tables()
    return {"migrated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


def create_database_backup():
    """Tạo bản sao SQLite để backup trước khi sửa dữ liệu lớn."""
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = BACKUP_ROOT / f"mecprecision-{timestamp}.sqlite"
    shutil.copy2(DATABASE_PATH, backup_path)
    return backup_path


def list_database_backups():
    """Liệt kê các file backup database đã tạo."""
    if not BACKUP_ROOT.exists():
        return []
    return sorted(
        [
            {
                "name": item.name,
                "path": str(item),
                "size": item.stat().st_size,
                "modified_at": datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            }
            for item in BACKUP_ROOT.glob("*.sqlite")
        ],
        key=lambda item: item["modified_at"],
        reverse=True,
    )

