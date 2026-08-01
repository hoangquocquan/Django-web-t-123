"""Test settings for the Django migration backend."""

from .base import *  # noqa: F401,F403


DEBUG = False
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
KNOWLEDGE_EMBEDDING_PROVIDER = "development-hash"
KNOWLEDGE_MIN_RELEVANCE_SCORE = 0.0
AI_SALES_OLLAMA_ENABLED = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
    "legacy": DATABASES["legacy"],
}

LOGGING["handlers"]["file"]["filename"] = LOG_DIR / "django-test.log"  # noqa: F405
