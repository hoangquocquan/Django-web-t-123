"""Tests for Phase 11.1.5.2 evidence and approval collection."""

from scripts.phase11_1_5_2_evidence_approval_validator import validate_evidence_approval


def complete_package():
    """Return a complete package that can approve shutdown readiness."""
    return {
        "evidence": {
            "legacy_requests": 0,
            "replacement_requests": 1200,
            "unknown_clients": 0,
            "logs_provided": True,
            "safe_to_decommission": True,
        },
        "approval": {
            "technical": True,
            "business": True,
            "rollback": True,
            "monitoring": True,
        },
        "clients": [
            {
                "client": "Frontend",
                "legacy_api_usage": "none",
                "replacement_api": "/api/v1/public/home/",
                "migration_completed": True,
                "confirmation_date": "2026-08-01",
            },
            {
                "client": "Internal scripts",
                "legacy_api_usage": "none",
                "replacement_api": "/api/v1/catalog/products/",
                "migration_completed": True,
                "confirmation_date": "2026-08-01",
            },
        ],
    }


def test_missing_evidence_blocked():
    """Default execution has no production evidence and must stay blocked."""
    result = validate_evidence_approval(env={}, package_data={})

    assert result["status"] == "KEEP_LEGACY_API_ACTIVE"
    assert "Production evidence logs are missing." in result["errors"]
    assert result["legacy_routes_disabled"] is False


def test_missing_approval_blocked():
    """Complete traffic evidence still needs approval fields."""
    package = complete_package()
    package["approval"] = {}

    result = validate_evidence_approval(package_data=package)

    assert result["status"] == "KEEP_LEGACY_API_ACTIVE"
    assert "Technical approval is missing." in result["errors"]
    assert "Business approval is missing." in result["errors"]


def test_incomplete_client_confirmation_blocked():
    """Every known client must confirm migration completion."""
    package = complete_package()
    package["clients"][0]["migration_completed"] = False

    result = validate_evidence_approval(package_data=package)

    assert result["status"] == "KEEP_LEGACY_API_ACTIVE"
    assert any("migration completion is not confirmed" in error for error in result["errors"])


def test_unknown_clients_blocked():
    """Unknown clients in evidence must keep legacy API active."""
    package = complete_package()
    package["evidence"]["unknown_clients"] = 1

    result = validate_evidence_approval(package_data=package)

    assert result["status"] == "KEEP_LEGACY_API_ACTIVE"
    assert "Unknown clients must equal zero." in result["errors"]


def test_complete_package_accepted():
    """Complete package can return READY_FOR_LEGACY_API_SHUTDOWN."""
    result = validate_evidence_approval(package_data=complete_package())

    assert result["status"] == "READY_FOR_LEGACY_API_SHUTDOWN"
    assert result["ready_for_shutdown"] is True
    assert result["routes_changed"] is False
