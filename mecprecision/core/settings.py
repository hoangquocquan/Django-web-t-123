"""Cấu hình Django nền tảng cho dự án MecPrecision.

File này mới là skeleton. Các module nghiệp vụ cũ vẫn đang chạy ở backend/app.py.
"""

from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "mecprecision-django-dev-secret")
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() in {"1", "true", "yes", "on"}
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

# Các biến này giúp Django dùng chung cấu hình với backend cũ trong giai đoạn migrate.
MEC_SESSION_TTL_SECONDS = int(os.environ.get("MEC_SESSION_TTL_SECONDS", str(60 * 60 * 8)))
MEC_PASSWORD_SALT = os.environ.get("MEC_PASSWORD_SALT", "mecprecision-demo-salt")
OLLAMA_URL = os.environ.get("MEC_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("MEC_OLLAMA_MODEL", "llama3:latest")
OLLAMA_TIMEOUT_SECONDS = int(os.environ.get("MEC_OLLAMA_TIMEOUT_SECONDS", "20"))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "products",
    "customers",
    "quotation",
    "news",
    "chatbot",
    "ai",
    "dashboard",
    "common",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "core.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get(
            "DJANGO_DATABASE_PATH",
            str(PROJECT_ROOT / "backend" / "database" / "mecprecision.sqlite"),
        ),
    }
}

LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
