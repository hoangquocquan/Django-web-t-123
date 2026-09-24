"""Contract tests for the first Phase 9 API cutover endpoint."""


import pytest


LEGACY_HEALTH_KEYS = {
    "status",
    "api_version",
    "environment",
    "database",
    "sqlite_version",
    "redis_enabled",
}


@pytest.mark.parametrize(
    "url",
    [
        "/api/health",
        "/api/health/",
        "/api/v1/health",
        "/api/v1/health/",
    ],
)
def test_health_cutover_preserves_legacy_contract(client, legacy_db, url):
    """Django must keep the same health payload shape as the legacy endpoint."""
    response = client.get(url)
    body = response.json()

    assert response.status_code == 200
    assert set(body.keys()) == LEGACY_HEALTH_KEYS
    assert body["status"] == "ok"
    assert body["api_version"] == "1.1.0"
    assert body["database"] == "ok"
    assert isinstance(body["redis_enabled"], bool)


def test_health_cutover_status_documents_route_switch(client):
    """The cutover status endpoint explains what route Django now serves."""
    response = client.get("/api/v1/cutover/health/")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["phase"] == 9
    assert body["cutover"]["endpoint"] == "/api/health"
    assert body["cutover"]["status"] == "enabled"
    assert body["compatibility_contract"]["write_api_cutover"] is False
    assert body["compatibility_contract"]["auth_cutover"] is False


def test_health_rollback_endpoint_is_read_only_smoke_test(client):
    """Rollback endpoint returns instructions only; it does not mutate config."""
    response = client.get("/api/v1/cutover/health/rollback/")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["rollback_ready"] is True
    assert body["safety"]["database_changed"] is False
    assert body["safety"]["legacy_code_changed"] is False
    assert body["safety"]["write_api_cutover"] is False


def test_health_cutover_rejects_write_method(client):
    """The first cutover endpoint is read-only and must reject POST writes."""
    response = client.post("/api/health", data={}, content_type="application/json")

    assert response.status_code == 405
    assert "detail" in response.json()
