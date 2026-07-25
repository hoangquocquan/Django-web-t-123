"""Fixture dùng chung cho toàn bộ test Django migration.

Đặt file ở root `django_backend` để cả test trong `tests/` và `apps/`
đều dùng được fixture `legacy_db`.
"""

from pathlib import Path
import sys

import pytest
from django.db import connections


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    # Thêm project root để import được script helper nằm ngoài django_backend.
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.copy_legacy_database_for_test import copy_legacy_database  # noqa: E402


@pytest.fixture
def legacy_db(settings, django_db_blocker, tmp_path):
    """Trỏ alias `legacy` sang bản copy read-only trong lúc chạy test."""
    copied_database = copy_legacy_database(
        destination=tmp_path / "legacy_database" / "mecprecision-test.sqlite"
    )

    # Lấy cấu hình đã được Django chuẩn hóa để không làm mất các key nội bộ
    # như TIME_ZONE, ATOMIC_REQUESTS, CONN_HEALTH_CHECKS.
    legacy_settings = connections.databases["legacy"].copy()
    legacy_settings["NAME"] = f"file:{copied_database.as_posix()}?mode=ro"
    legacy_settings["OPTIONS"] = {"uri": True}

    settings.DATABASES["legacy"] = legacy_settings
    connections.databases["legacy"] = legacy_settings
    connections["legacy"].close()

    with django_db_blocker.unblock():
        yield copied_database

    connections["legacy"].close()
