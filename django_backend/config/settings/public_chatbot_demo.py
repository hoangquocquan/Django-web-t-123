"""Settings for the isolated public-chatbot verification database."""

from copy import deepcopy
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from .development import *  # noqa: F401,F403


PUBLIC_CHATBOT_DEMO_ISOLATED = True

_configured_path = os.getenv("PUBLIC_CHATBOT_DEMO_DB_PATH", "").strip()
if not _configured_path:
    raise ImproperlyConfigured(
        "PUBLIC_CHATBOT_DEMO_DB_PATH is required for the isolated chatbot demo."
    )

PUBLIC_CHATBOT_DEMO_DB_PATH = Path(_configured_path).expanduser().resolve()
_main_demo_path = (BASE_DIR / "db.sqlite3").resolve()  # noqa: F405
if PUBLIC_CHATBOT_DEMO_DB_PATH == _main_demo_path:
    raise ImproperlyConfigured(
        "The isolated chatbot demo must not use the main db.sqlite3 database."
    )
if not PUBLIC_CHATBOT_DEMO_DB_PATH.is_file():
    raise ImproperlyConfigured(
        f"The isolated chatbot demo database does not exist: {PUBLIC_CHATBOT_DEMO_DB_PATH}"
    )

DATABASES = deepcopy(DATABASES)  # noqa: F405
DATABASES["default"] = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": PUBLIC_CHATBOT_DEMO_DB_PATH,
}

