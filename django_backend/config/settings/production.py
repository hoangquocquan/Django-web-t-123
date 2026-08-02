"""Production settings for the Django migration backend."""

import os
from copy import deepcopy
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403


def required_environment(name):
    """Return a required production value or stop before Django starts."""
    value = os.getenv(name, "").strip()
    if not value:
        raise ImproperlyConfigured(
            f"Production environment variable {name} is required."
        )
    return value


DEBUG = False
ENVIRONMENT = "production"

MIDDLEWARE = [*MIDDLEWARE]  # noqa: F405
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

DATABASES = deepcopy(DATABASES)  # noqa: F405
LOGGING = deepcopy(LOGGING)  # noqa: F405

SECRET_KEY = required_environment("SECRET_KEY")
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")  # noqa: F405
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "Production ALLOWED_HOSTS must contain at least one host."
    )

DATABASE_URL = required_environment("DATABASE_URL")
if urlparse(DATABASE_URL).scheme not in {"postgres", "postgresql"}:
    raise ImproperlyConfigured("Production DATABASE_URL must use PostgreSQL.")
DATABASES["default"] = database_from_url(DATABASE_URL)  # noqa: F405
DATABASES["default"].update(
    {
        "CONN_MAX_AGE": env_int("DATABASE_CONN_MAX_AGE", 60),  # noqa: F405
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {"sslmode": os.getenv("DATABASE_SSLMODE", "prefer")},
    }
)

REDIS_URL = required_environment("REDIS_URL")
if urlparse(REDIS_URL).scheme not in {"redis", "rediss"}:
    raise ImproperlyConfigured("Production REDIS_URL must use redis:// or rediss://.")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "TIMEOUT": env_int("CACHE_DEFAULT_TIMEOUT", 300),  # noqa: F405
        "KEY_PREFIX": os.getenv("CACHE_KEY_PREFIX", "mecprecision"),
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
AI_REDIS_RATE_LIMIT_ENABLED = True
AI_OLLAMA_CAPACITY_ENABLED = True

SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)  # noqa: F405
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", True)  # noqa: F405
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", True)  # noqa: F405
CSRF_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)  # noqa: F405
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", True)  # noqa: F405
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")  # noqa: F405

STATIC_ROOT = Path(os.getenv("STATIC_ROOT", BASE_DIR / "staticfiles"))  # noqa: F405
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", BASE_DIR / "media"))  # noqa: F405
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
        "formatter": "standard",
    }
}
production_loggers = cast(dict[str, dict[str, object]], LOGGING["loggers"])
for logger in production_loggers.values():
    logger["handlers"] = ["console"]
