from pathlib import Path

import pytest
from django.urls import reverse


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_legacy_ai_files_are_archived_and_removed_from_runtime():
    """Legacy AI code is backed up but no longer loaded from backend runtime folders."""
    assert (PROJECT_ROOT / "archive" / "legacy_ai" / "backend" / "services" / "ai_service.py").exists()
    assert (PROJECT_ROOT / "archive" / "legacy_ai" / "backend" / "repositories" / "ai_repository.py").exists()
    assert not (PROJECT_ROOT / "backend" / "services" / "ai_service.py").exists()
    assert not (PROJECT_ROOT / "backend" / "repositories" / "ai_repository.py").exists()


def test_legacy_backend_is_retired_from_runtime():
    """The retired custom backend must not be restored beside Django."""
    assert not (PROJECT_ROOT / "backend").exists()
    assert (PROJECT_ROOT / "django_backend" / "config" / "urls.py").exists()


def test_legacy_openapi_module_is_not_part_of_runtime():
    """Only the canonical Django route surface remains executable."""
    assert not (PROJECT_ROOT / "backend" / "api" / "openapi.py").exists()
    assert reverse("api-ai-chat") == "/api/v1/ai/chat/"


@pytest.mark.django_db
def test_django_ai_platform_routes_remain_available(client):
    """New Django AI platform endpoints remain registered and protected by auth."""
    assert reverse("api-ai-chat") == "/api/v1/ai/chat/"
    assert reverse("api-knowledge-chat") == "/api/v1/knowledge/chat/"
    assert reverse("api-ai-sales-assistant") == "/api/v1/ai/sales-assistant/"

    assert client.post("/api/v1/ai/chat/", data={}, content_type="application/json").status_code == 403
    assert client.post("/api/v1/knowledge/chat/", data={}, content_type="application/json").status_code == 403
    assert client.post("/api/v1/ai/sales-assistant/", data={}, content_type="application/json").status_code == 403
