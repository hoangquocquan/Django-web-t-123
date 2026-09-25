"""Base Django settings shared by all environments.

Phase 2 is foundation-only. This file configures infrastructure such as apps,
middleware, database connection, logging, static/media paths, and DRF. It does
not define business models or migrate legacy data.
"""

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    """Read a boolean value from environment variables."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    """Read a comma-separated list from environment variables."""
    return [
        item.strip() for item in os.getenv(name, default).split(",") if item.strip()
    ]


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
    "apps.common.middleware.ObservabilityMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.common.middleware.SecurityHeadersMiddleware",
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
}

# The retired backend database is compatibility-only. A fresh clone must not
# depend on an ignored local SQLite file or silently create one. Operators who
# still need read-only compatibility must opt in and provide an explicit URI.
LEGACY_DATABASE_ENABLED = env_bool("LEGACY_DATABASE_ENABLED", False)
LEGACY_DATABASE_URL = os.getenv("LEGACY_DATABASE_URL", "").strip()
if LEGACY_DATABASE_ENABLED:
    if not LEGACY_DATABASE_URL:
        raise ImproperlyConfigured(
            "LEGACY_DATABASE_URL is required when LEGACY_DATABASE_ENABLED=true."
        )
    DATABASES["legacy"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": LEGACY_DATABASE_URL,
        "OPTIONS": {"uri": LEGACY_DATABASE_URL.startswith("file:")},
    }


REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.api.authentication.FoundationBearerAuthentication",
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
        "json": {
            "()": "apps.common.logging.JsonLogFormatter",
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
        "apps.operations": {
            "handlers": ["console", "file"],
            "level": os.getenv("OPERATIONS_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_GENERATION_MODELS = tuple(
    item.strip()
    for item in os.getenv("OLLAMA_GENERATION_MODELS", f"{OLLAMA_MODEL},llama3.1").split(
        ","
    )
    if item.strip()
)
OLLAMA_REVIEW_MODEL = os.getenv("OLLAMA_REVIEW_MODEL", OLLAMA_MODEL)
OLLAMA_REVIEW_MODELS = tuple(
    item.strip()
    for item in os.getenv("OLLAMA_REVIEW_MODELS", OLLAMA_REVIEW_MODEL).split(",")
    if item.strip()
)
OLLAMA_TIMEOUT_SECONDS = env_int("OLLAMA_TIMEOUT_SECONDS", 30)
OLLAMA_TEMPERATURE = env_float("OLLAMA_TEMPERATURE", 0.2)
OLLAMA_NUM_PREDICT = env_int("OLLAMA_NUM_PREDICT", 512)
AI_SALES_OLLAMA_ENABLED = env_bool("AI_SALES_OLLAMA_ENABLED", True)
AI_SALES_KNOWLEDGE_SOURCE = os.getenv(
    "AI_SALES_KNOWLEDGE_SOURCE", "governed_synthetic"
)
AI_SALES_SYNTHESIS_ATTEMPTS = env_int("AI_SALES_SYNTHESIS_ATTEMPTS", 2)
AI_AGENT_OLLAMA_PLANNER_ENABLED = env_bool("AI_AGENT_OLLAMA_PLANNER_ENABLED", True)
AI_AGENT_MAX_STEPS = env_int("AI_AGENT_MAX_STEPS", 5)
AI_AGENT_TOTAL_TIMEOUT_SECONDS = env_float("AI_AGENT_TOTAL_TIMEOUT_SECONDS", 20)
AI_AGENT_MAX_CONTEXT_CHARS = env_int("AI_AGENT_MAX_CONTEXT_CHARS", 12000)
AI_AGENT_MAX_TOOL_OUTPUT_CHARS = env_int("AI_AGENT_MAX_TOOL_OUTPUT_CHARS", 4000)
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_EMBEDDING_MODELS = tuple(
    item.strip()
    for item in os.getenv("OLLAMA_EMBEDDING_MODELS", OLLAMA_EMBEDDING_MODEL).split(",")
    if item.strip()
)
OLLAMA_EMBEDDING_TIMEOUT_SECONDS = env_int("OLLAMA_EMBEDDING_TIMEOUT_SECONDS", 30)
OLLAMA_EMBEDDING_RETRIES = env_int("OLLAMA_EMBEDDING_RETRIES", 1)
OLLAMA_EMBEDDING_DIMENSIONS = env_int("OLLAMA_EMBEDDING_DIMENSIONS", 768)
KNOWLEDGE_EMBEDDING_PROVIDER = os.getenv("KNOWLEDGE_EMBEDDING_PROVIDER", "ollama")
KNOWLEDGE_MIN_RELEVANCE_SCORE = env_float("KNOWLEDGE_MIN_RELEVANCE_SCORE", 0.5)
PUBLIC_AI_ENABLED = False  # Separate release approval is required; not environment-overridable here.
PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED = False  # Never expose internal synthetic data by default.
AI_PILOT_CORPUS_MAX_DOCUMENTS = 100
AI_PILOT_CORPUS_MIN_DOCUMENTS = 50
AI_CHAT_MAX_MESSAGE_LENGTH = env_int("AI_CHAT_MAX_MESSAGE_LENGTH", 2000)
AI_RATE_LIMIT_PER_USER = env_int("AI_RATE_LIMIT_PER_USER", 30)
AI_RATE_LIMIT_WINDOW_SECONDS = env_int("AI_RATE_LIMIT_WINDOW_SECONDS", 60)
AI_POLICY_VERSION = os.getenv("AI_POLICY_VERSION", "ai-policy-v2.0")
AI_MAX_INPUT_CHARS = env_int("AI_MAX_INPUT_CHARS", 12000)
REDIS_URL = os.getenv("REDIS_URL", "")
AI_REDIS_RATE_LIMIT_ENABLED = env_bool("AI_REDIS_RATE_LIMIT_ENABLED", False)
AI_OLLAMA_CAPACITY_ENABLED = env_bool("AI_OLLAMA_CAPACITY_ENABLED", False)
AI_OLLAMA_MAX_CONCURRENCY = env_int("AI_OLLAMA_MAX_CONCURRENCY", 2)
AI_OLLAMA_LEASE_SECONDS = env_int("AI_OLLAMA_LEASE_SECONDS", 120)
AUTH_PASSWORD_MIN_LENGTH = env_int("AUTH_PASSWORD_MIN_LENGTH", 12)
AUTH_LOGIN_MAX_FAILURES = env_int("AUTH_LOGIN_MAX_FAILURES", 5)
AUTH_LOGIN_WINDOW_SECONDS = env_int("AUTH_LOGIN_WINDOW_SECONDS", 900)
AUTH_TOKEN_TTL_HOURS = env_int("AUTH_TOKEN_TTL_HOURS", 8)
AUTH_MAX_ACTIVE_TOKENS = env_int("AUTH_MAX_ACTIVE_TOKENS", 5)
UPLOAD_MAX_BYTES = env_int("UPLOAD_MAX_BYTES", 10 * 1024 * 1024)
UPLOAD_ARCHIVE_MAX_MEMBERS = env_int("UPLOAD_ARCHIVE_MAX_MEMBERS", 500)
UPLOAD_ARCHIVE_MAX_UNCOMPRESSED_BYTES = env_int(
    "UPLOAD_ARCHIVE_MAX_UNCOMPRESSED_BYTES", 50 * 1024 * 1024
)
UPLOAD_ARCHIVE_MAX_RATIO = env_int("UPLOAD_ARCHIVE_MAX_RATIO", 100)
ALLOWED_EXTERNAL_HOSTS = env_list("ALLOWED_EXTERNAL_HOSTS", "")
METRICS_BEARER_TOKEN = os.getenv("METRICS_BEARER_TOKEN", "")
N8N_HEALTH_URL = os.getenv("N8N_HEALTH_URL", "http://localhost:5679/healthz")
