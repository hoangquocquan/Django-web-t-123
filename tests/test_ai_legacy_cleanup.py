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


def test_legacy_backend_no_longer_imports_ai_service():
    """The custom backend should not import old AI services after cleanup."""
    app_source = (PROJECT_ROOT / "backend" / "app.py").read_text(encoding="utf-8")
    localization_source = (PROJECT_ROOT / "backend" / "services" / "localization_service.py").read_text(encoding="utf-8")

    assert "from services.ai_service" not in app_source
    assert "from services.ai_service" not in localization_source
    assert "/api/ai/chat" not in app_source


def test_legacy_openapi_no_longer_contains_ai_chat():
    """Legacy OpenAPI should point users away from old AI routes."""
    import sys

    backend_root = PROJECT_ROOT / "backend"
    sys.path.insert(0, str(backend_root))
    try:
        from api.openapi import get_openapi_schema

        schema = get_openapi_schema()
    finally:
        sys.path.remove(str(backend_root))

    assert "/api/ai/chat" not in schema["paths"]


@pytest.mark.django_db
def test_django_ai_platform_routes_remain_available(client):
    """New Django AI platform endpoints remain registered and protected by auth."""
    assert reverse("api-ai-chat") == "/api/v1/ai/chat/"
    assert reverse("api-knowledge-chat") == "/api/v1/knowledge/chat/"
    assert reverse("api-ai-sales-assistant") == "/api/v1/ai/sales-assistant/"

    assert client.post("/api/v1/ai/chat/", data={}, content_type="application/json").status_code == 403
    assert client.post("/api/v1/knowledge/chat/", data={}, content_type="application/json").status_code == 403
    assert client.post("/api/v1/ai/sales-assistant/", data={}, content_type="application/json").status_code == 403
