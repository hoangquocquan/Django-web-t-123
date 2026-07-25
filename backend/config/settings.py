import os
from pathlib import Path


# Cấu hình đường dẫn và thông số chạy server tập trung tại một nơi.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
UPLOAD_ROOT = BACKEND_ROOT / "uploads"
LOG_ROOT = BACKEND_ROOT / "logs"


def load_env_file(path):
    """Đọc file .env đơn giản để tách cấu hình dev/test/production."""
    # File .env thường chứa cấu hình riêng từng môi trường.
    # Ví dụ: MEC_ENV=development, MEC_PORT=8000, MEC_DATABASE_PATH=...
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_bool_env(name, default=False):
    """Đổi biến môi trường dạng text sang boolean."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


load_env_file(PROJECT_ROOT / ".env")

ENVIRONMENT = os.environ.get("MEC_ENV", "development")
DEBUG = get_bool_env("MEC_DEBUG", ENVIRONMENT != "production")

HOST = os.environ.get("MEC_HOST", "127.0.0.1")
PORT = int(os.environ.get("MEC_PORT", "8000"))

DATABASE_PATH = Path(
    os.environ.get("MEC_DATABASE_PATH", str(BACKEND_ROOT / "database" / "mecprecision.sqlite"))
)

SESSION_COOKIE_NAME = "mecprecision_session"
SESSION_TTL_SECONDS = int(os.environ.get("MEC_SESSION_TTL_SECONDS", str(60 * 60 * 8)))

LOGIN_RATE_LIMIT_WINDOW_SECONDS = 60 * 5
LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 5

PASSWORD_SALT = os.environ.get("MEC_PASSWORD_SALT", "mecprecision-demo-salt")

# Redis là tùy chọn. Local chưa cần Redis vẫn chạy bình thường.
# Khi production cần cache/session nhanh hơn, bật MEC_REDIS_URL trong .env.
REDIS_URL = os.environ.get("MEC_REDIS_URL", "")
REDIS_CACHE_ENABLED = get_bool_env("MEC_REDIS_CACHE_ENABLED", False)

# Ollama local AI. Khi production có AI server riêng, chỉ cần đổi các biến này trong .env.
OLLAMA_URL = os.environ.get("MEC_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("MEC_OLLAMA_MODEL", "llama3:latest")
OLLAMA_TIMEOUT_SECONDS = int(os.environ.get("MEC_OLLAMA_TIMEOUT_SECONDS", "20"))
