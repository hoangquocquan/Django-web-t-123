"""Production settings for the Django migration backend."""

import os
from copy import deepcopy
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

from .base import *


def required_environment(name):
    """Return a required production value or stop before Django starts."""
    value = os.getenv(name, "").strip()
    if not value:
        raise ImproperlyConfigured(
            f"Production environment variable {name} is required."
        )
    return value


def required_boolean_environment(name):
    """Return an explicitly configured production boolean."""
    value = required_environment(name).casefold()
    if value not in {"true", "false"}:
        raise ImproperlyConfigured(
            f"Production environment variable {name} must be true or false."
        )
    return value == "true"


def validated_url(name, schemes, *, require_username=False, require_password=False):
    """Return a bounded production service URL or fail without echoing it."""
    value = required_environment(name)
    parsed = urlparse(value)
    if (
        parsed.scheme not in schemes
        or not parsed.hostname
        or parsed.fragment
        or (require_username and not parsed.username)
        or (require_password and not parsed.password)
    ):
        allowed = " or ".join(f"{scheme}://" for scheme in sorted(schemes))
        raise ImproperlyConfigured(
            f"Production {name} must be a complete {allowed} service URL."
        )
    return value, parsed


DEBUG = False
ENVIRONMENT = "production"

MIDDLEWARE = [*MIDDLEWARE]
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

DATABASES = deepcopy(DATABASES)
LOGGING = deepcopy(LOGGING)

SECRET_KEY = required_environment("SECRET_KEY")
if SECRET_KEY.upper() == "CHANGE_ME" or any(char in SECRET_KEY for char in "\r\n\x00"):
    raise ImproperlyConfigured(
        "Production SECRET_KEY contains an unsafe placeholder or control character."
    )
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "Production ALLOWED_HOSTS must contain at least one host."
    )
if any(
    host == "*" or "://" in host or "/" in host or any(char.isspace() for char in host)
    for host in ALLOWED_HOSTS
):
    raise ImproperlyConfigured(
        "Production ALLOWED_HOSTS must contain explicit host names only."
    )

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
if CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured(
        "Production CORS_ALLOWED_ORIGINS must be empty for the same-origin deployment."
    )

DATABASE_URL, parsed_database_url = validated_url(
    "DATABASE_URL",
    {"postgres", "postgresql"},
    require_username=True,
    require_password=True,
)
if not parsed_database_url.path.strip("/"):
    raise ImproperlyConfigured(
        "Production DATABASE_URL must name a PostgreSQL database."
    )
DATABASES["default"] = database_from_url(DATABASE_URL)
DATABASE_SSLMODE = required_environment("DATABASE_SSLMODE").casefold()
if DATABASE_SSLMODE not in {"require", "verify-full"}:
    raise ImproperlyConfigured(
        "Production DATABASE_SSLMODE must be require or verify-full."
    )
DATABASES["default"].update(
    {
        "CONN_MAX_AGE": env_int("DATABASE_CONN_MAX_AGE", 60),
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "sslmode": DATABASE_SSLMODE,
            "connect_timeout": env_int("DATABASE_CONNECT_TIMEOUT_SECONDS", 5),
        },
    }
)

REDIS_URL, _parsed_redis_url = validated_url(
    "REDIS_URL", {"redis", "rediss"}, require_password=True
)
if _parsed_redis_url.scheme != "rediss":
    raise ImproperlyConfigured("Production REDIS_URL must use TLS (rediss://).")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "TIMEOUT": env_int("CACHE_DEFAULT_TIMEOUT", 300),
        "KEY_PREFIX": os.getenv("CACHE_KEY_PREFIX", "mecprecision"),
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
AI_SALES_OLLAMA_ENABLED = required_boolean_environment("AI_SALES_OLLAMA_ENABLED")
AI_AGENT_OLLAMA_PLANNER_ENABLED = required_boolean_environment(
    "AI_AGENT_OLLAMA_PLANNER_ENABLED"
)
AI_REDIS_RATE_LIMIT_ENABLED = required_boolean_environment(
    "AI_REDIS_RATE_LIMIT_ENABLED"
)
AI_OLLAMA_CAPACITY_ENABLED = required_boolean_environment(
    "AI_OLLAMA_CAPACITY_ENABLED"
)
if AI_SALES_OLLAMA_ENABLED or AI_AGENT_OLLAMA_PLANNER_ENABLED or AI_OLLAMA_CAPACITY_ENABLED:
    OLLAMA_HOST, parsed_ollama_host = validated_url("OLLAMA_HOST", {"http", "https"})
    if parsed_ollama_host.hostname in {"localhost", "127.0.0.1", "::1"}:
        raise ImproperlyConfigured(
            "Production OLLAMA_HOST must identify an explicitly provisioned provider."
        )
if LINE_SEND_ENABLED:
    raise ImproperlyConfigured("Production LINE_SEND_ENABLED must remain false.")
if LEGACY_DATABASE_ENABLED:
    raise ImproperlyConfigured("Production LEGACY_DATABASE_ENABLED must remain false.")
if PUBLIC_AI_ENABLED or PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED:
    raise ImproperlyConfigured("Production anonymous AI feature flags must remain false.")
METRICS_BEARER_TOKEN = required_environment("METRICS_BEARER_TOKEN")

SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", True)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", True)
CSRF_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", True)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
for origin in CSRF_TRUSTED_ORIGINS:
    parsed_origin = urlparse(origin)
    if (
        parsed_origin.scheme not in {"http", "https"}
        or not parsed_origin.hostname
        or parsed_origin.username
        or parsed_origin.password
        or parsed_origin.path not in {"", "/"}
        or parsed_origin.query
        or parsed_origin.fragment
        or "*" in origin
    ):
        raise ImproperlyConfigured(
            "Production CSRF_TRUSTED_ORIGINS must contain explicit HTTP(S) origins only."
        )
    if SECURE_SSL_REDIRECT and parsed_origin.scheme != "https":
        raise ImproperlyConfigured(
            "Production CSRF_TRUSTED_ORIGINS must use HTTPS when SSL redirect is enabled."
        )

STATIC_ROOT = Path(os.getenv("STATIC_ROOT", BASE_DIR / "staticfiles"))
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", BASE_DIR / "media"))
MEDIA_STORAGE_DURABLE = env_strict_true("MEDIA_STORAGE_DURABLE")
MEDIA_BACKUP_ENABLED = env_strict_true("MEDIA_BACKUP_ENABLED")
if not MEDIA_STORAGE_DURABLE or not MEDIA_BACKUP_ENABLED:
    raise ImproperlyConfigured(
        "Production media requires MEDIA_STORAGE_DURABLE=true and MEDIA_BACKUP_ENABLED=true."
    )
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# Production logs go to stdout/stderr so the container platform can rotate and
# aggregate them. Runtime log files are deliberately not written into the image.
LOGGING["handlers"] = {
    "console": {
        "class": "logging.StreamHandler",
        "formatter": "json",
    }
}
production_loggers = cast(dict[str, dict[str, object]], LOGGING["loggers"])
for logger in production_loggers.values():
    logger["handlers"] = ["console"]
