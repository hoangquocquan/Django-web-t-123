"""Development settings for the Django migration backend."""

from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403


DEBUG = True
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")  # noqa: F405

for origin in CORS_ALLOWED_ORIGINS:  # noqa: F405
    parsed = urlparse(origin)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or not parsed.port
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ImproperlyConfigured(
            "Development CORS_ALLOWED_ORIGINS must contain explicit loopback HTTP origins."
        )

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
