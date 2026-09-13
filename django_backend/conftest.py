"""Fixture dùng chung cho toàn bộ test Django migration.

Đặt file ở root `django_backend` để cả test trong `tests/` và `apps/`
đều dùng được fixture `legacy_db`.
"""

import os
from pathlib import Path
import sys
from urllib.parse import unquote, urlparse

import pytest
from django.db import connections
from django.db.migrations.executor import MigrationExecutor


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    # Thêm project root để import được script helper nằm ngoài django_backend.
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.copy_legacy_database_for_test import copy_legacy_database  # noqa: E402


LEGACY_ARTIFACT_SKIP_REASON = (
    "legacy SQLite artifact is not available in a fresh clone"
)


def configured_legacy_artifact_path():
    """Return the explicitly enabled read-only legacy SQLite path, if valid."""
    enabled = os.getenv("LEGACY_DATABASE_ENABLED", "").strip().lower()
    if enabled not in {"1", "true", "yes", "on"}:
        return None

    database_url = os.getenv("LEGACY_DATABASE_URL", "").strip()
    if not database_url.startswith("file:") or "mode=ro" not in database_url:
        return None

    parsed = urlparse(database_url)
    database_path = unquote(parsed.path)
    if parsed.netloc:
        database_path = f"//{parsed.netloc}{database_path}"
    if len(database_path) > 2 and database_path[0] == "/" and database_path[2] == ":":
        database_path = database_path[1:]

    path = Path(database_path)
    return path if path.is_file() else None


def pytest_collection_modifyitems(items):
    """Classify and conditionally skip only tests needing the legacy artifact."""
    artifact_available = configured_legacy_artifact_path() is not None
    for item in items:
        if "legacy_db" in item.fixturenames or "legacy_artifact_path" in item.fixturenames:
            item.add_marker(pytest.mark.legacy_artifact)
        if item.get_closest_marker("legacy_artifact") and not artifact_available:
            item.add_marker(pytest.mark.skip(reason=LEGACY_ARTIFACT_SKIP_REASON))


@pytest.fixture
def legacy_artifact_path():
    """Expose an Owner-provided artifact only after explicit read-only opt-in."""
    path = configured_legacy_artifact_path()
    if path is None:
        pytest.skip(LEGACY_ARTIFACT_SKIP_REASON)
    return path


@pytest.fixture
def legacy_db(settings, django_db_blocker, tmp_path, legacy_artifact_path):
    """Trỏ alias `legacy` sang bản copy read-only trong lúc chạy test."""
    try:
        copied_database = copy_legacy_database(
            source=legacy_artifact_path,
            destination=tmp_path / "legacy_database" / "mecprecision-test.sqlite"
        )
    except FileNotFoundError as exc:
        pytest.skip(f"{LEGACY_ARTIFACT_SKIP_REASON}: {exc}")

    # Tests opt in explicitly to a disposable read-only copy. Production and a
    # fresh development clone do not register this database alias by default.
    legacy_settings = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": f"file:{copied_database.as_posix()}?mode=ro",
        "OPTIONS": {"uri": True},
        "ATOMIC_REQUESTS": False,
        "AUTOCOMMIT": True,
        "CONN_HEALTH_CHECKS": False,
        "CONN_MAX_AGE": 0,
        "TIME_ZONE": None,
        "TEST": {
            "CHARSET": None,
            "COLLATION": None,
            "MIGRATE": True,
            "MIRROR": None,
            "NAME": None,
        },
    }

    settings.DATABASES["legacy"] = legacy_settings
    connections.databases["legacy"] = legacy_settings
    connections["legacy"].close()

    with django_db_blocker.unblock():
        yield copied_database

    connections["legacy"].close()
    del connections.databases["legacy"]
    settings.DATABASES.pop("legacy", None)


@pytest.fixture(autouse=True)
def restore_latest_schema_after_phase3_migration_boundary(request, django_db_blocker):
    """Keep migration-boundary tests from leaking historical schema to later tests."""
    yield
    migration_modules = {
        "test_phase3b_migrations.py",
        "test_phase3c_migrations.py",
        "test_phase3d_migrations.py",
    }
    if request.node.path.name not in migration_modules:
        return
    with django_db_blocker.unblock():
        default_connection = connections["default"]
        executor = MigrationExecutor(default_connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
