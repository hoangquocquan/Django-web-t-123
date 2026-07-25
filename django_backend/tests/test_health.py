"""Tests for Phase 2 infrastructure health endpoints."""


def test_api_v1_health_returns_phase_2_ready(client):
    """The versioned health API proves the Django foundation is reachable."""
    response = client.get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Django foundation ready",
        "phase": 2,
    }
