"""Base Django settings shared by all environments.

Phase 2 is foundation-only. This file configures infrastructure such as apps,
middleware, database connection, logging, static/media paths, and DRF. It does
not define business models or migrate legacy data.
"""

from pathlib import Path
import os
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BASE_DIR.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    """Read a boolean value from environment variables."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    """Read a comma-separated list from environment variables."""
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def env_int(name, default):
    """Read an integer value from environment variables."""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def env_float(name, default):
    """Read a float value from environment variables."""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def database_from_url(database_url):
    """Convert DATABASE_URL into a Django database configuration.

    SQLite is the current development fallback. PostgreSQL is prepared for a
    later phase, but Phase 2 does not migrate any data or create ORM models.
    """
    if not database_url:
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }

    parsed = urlparse(database_url)

    if parsed.scheme in {"sqlite", "sqlite3"}:
        db_path = unquote(parsed.path)
        if parsed.netloc:
            db_path = f"//{parsed.netloc}{db_path}"
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": db_path or BASE_DIR / "db.sqlite3",
        }

    if parsed.scheme in {"postgres", "postgresql"}:
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(parsed.path.lstrip("/")),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "",
            "PORT": str(parsed.port or ""),
        }

    return {
        "ENGINE": os.getenv("DATABASE_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DATABASE_NAME", str(BASE_DIR / "db.sqlite3")),
    }


SECRET_KEY = os.getenv("SECRET_KEY", "django-phase-2-dev-only-secret-key")
DEBUG = env_bool("DEBUG", False)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "apps.admin_ui",
    "apps.business_ui",
    "apps.website",
    "apps.core",
    "apps.common",
    "apps.api",
    "apps.catalog",
    "apps.crm",
    "apps.sales",
    "apps.cms",
    "apps.accounts",
    "apps.newsletter",
    "apps.foundation",
    "apps.business_core",
    "apps.transaction_domain",
    "apps.ai",
    "apps.knowledge",
    "apps.ai_agent",
]


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]


DATABASES = {
    "default": database_from_url(os.getenv("DATABASE_URL", "")),
    "legacy": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv(
            "LEGACY_DATABASE_URL",
            f"file:{(PROJECT_ROOT / 'backend' / 'database' / 'mecprecision.sqlite').as_posix()}?mode=ro",
        ),
        "OPTIONS": {
            "uri": True,
        },
    },
}


REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}


LANGUAGE_CODE = "vi"
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Tokyo")
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "django.log",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "formatter": "standard",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "file"],
            "level": os.getenv("APP_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_TIMEOUT_SECONDS = env_int("OLLAMA_TIMEOUT_SECONDS", 30)
OLLAMA_TEMPERATURE = env_float("OLLAMA_TEMPERATURE", 0.2)
OLLAMA_NUM_PREDICT = env_int("OLLAMA_NUM_PREDICT", 512)
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_EMBEDDING_TIMEOUT_SECONDS = env_int("OLLAMA_EMBEDDING_TIMEOUT_SECONDS", 30)
OLLAMA_EMBEDDING_RETRIES = env_int("OLLAMA_EMBEDDING_RETRIES", 1)
OLLAMA_EMBEDDING_DIMENSIONS = env_int("OLLAMA_EMBEDDING_DIMENSIONS", 768)
KNOWLEDGE_EMBEDDING_PROVIDER = os.getenv("KNOWLEDGE_EMBEDDING_PROVIDER", "ollama")
KNOWLEDGE_MIN_RELEVANCE_SCORE = env_float("KNOWLEDGE_MIN_RELEVANCE_SCORE", 0.5)
AI_CHAT_MAX_MESSAGE_LENGTH = env_int("AI_CHAT_MAX_MESSAGE_LENGTH", 2000)
AI_RATE_LIMIT_PER_USER = env_int("AI_RATE_LIMIT_PER_USER", 30)
AI_RATE_LIMIT_WINDOW_SECONDS = env_int("AI_RATE_LIMIT_WINDOW_SECONDS", 60)
