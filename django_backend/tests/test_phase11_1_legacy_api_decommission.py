"""Tests cho cổng kiểm tra decommission legacy API Phase 11.1."""

from scripts.phase11_1_legacy_api_decommission_readiness import (
    evaluate_api_decommission_readiness,
)


def test_phase11_1_blocks_by_default():
    """Không có evidence production thì legacy API phải tiếp tục hoạt động."""
    result = evaluate_api_decommission_readiness({})

    assert result["status"] == "blocked_safely"
    assert result["legacy_api_decommission_recommendation"] == "KEEP_LEGACY_API_ACTIVE"
    assert result["legacy_routes_disabled"] is False
    assert result["legacy_routes_removed"] is False
    assert result["database_changed"] is False


def test_phase11_1_blocks_when_traffic_log_is_missing_after_replacements():
    """Có đủ replacement nhưng thiếu traffic log thì vẫn chưa được decommission."""
    env = {
        "PHASE11_1_DJANGO_API_CONTRACTS_VERIFIED": "verified",
        "PHASE11_1_ZERO_LEGACY_API_TRAFFIC_CONFIRMED": "verified",
        "PHASE11_1_CLIENT_CONTRACT_TESTS_PASSED": "passed",
        "PHASE11_1_ROLLBACK_WINDOW_RESPECTED": "approved",
        "PHASE11_1_ACCESS_LOGS_ARCHIVED": "verified",
        "PHASE11_1_DECOMMISSION_APPROVAL_ID": "APPROVAL-11.1",
    }

    result = evaluate_api_decommission_readiness(env)

    assert result["status"] == "blocked_safely"
    assert result["route_mapping"]["not_ready_count"] == 0
    assert "Traffic log path was not provided." in result["errors"]
    assert result["compatibility_adapters_removed"] is False


def test_phase11_1_can_be_ready_when_all_routes_and_evidence_are_mocked(tmp_path):
    """Khi mọi route có replacement và traffic log sạch, script chỉ cho review thủ công."""
    clean_log = tmp_path / "access.log"
    clean_log.write_text("GET / 200\nGET /api/v1/catalog/products/ 200\n", encoding="utf-8")
    env = {
        "PHASE11_1_DJANGO_API_CONTRACTS_VERIFIED": "verified",
        "PHASE11_1_ZERO_LEGACY_API_TRAFFIC_CONFIRMED": "verified",
        "PHASE11_1_CLIENT_CONTRACT_TESTS_PASSED": "passed",
        "PHASE11_1_ROLLBACK_WINDOW_RESPECTED": "approved",
        "PHASE11_1_ACCESS_LOGS_ARCHIVED": "verified",
        "PHASE11_1_DECOMMISSION_APPROVAL_ID": "APPROVAL-11.1",
        "PHASE11_1_LEGACY_TRAFFIC_LOG": str(clean_log),
    }
    mocked_routes = [
        {
            "method": "GET",
            "legacy_path": "/api/products",
            "django_replacement": "/api/v1/catalog/products/",
            "replacement_ready": True,
            "notes": "mocked replacement",
        }
    ]

    result = evaluate_api_decommission_readiness(env, routes=mocked_routes)

    assert result["status"] == "ready_for_manual_decommission_review"
    assert result["legacy_api_decommission_recommendation"] == "ALLOW_MANUAL_DECOMMISSION_REVIEW"
    assert result["legacy_routes_disabled"] is False


def test_phase11_1_blocks_when_traffic_log_contains_legacy_api_hits(tmp_path):
    """Nếu log còn request `/api/` legacy thì không được disable endpoint."""
    traffic_log = tmp_path / "access.log"
    traffic_log.write_text("GET /api/products 200\n", encoding="utf-8")
    env = {
        "PHASE11_1_DJANGO_API_CONTRACTS_VERIFIED": "verified",
        "PHASE11_1_ZERO_LEGACY_API_TRAFFIC_CONFIRMED": "verified",
        "PHASE11_1_CLIENT_CONTRACT_TESTS_PASSED": "passed",
        "PHASE11_1_ROLLBACK_WINDOW_RESPECTED": "approved",
        "PHASE11_1_ACCESS_LOGS_ARCHIVED": "verified",
        "PHASE11_1_DECOMMISSION_APPROVAL_ID": "APPROVAL-11.1",
        "PHASE11_1_LEGACY_TRAFFIC_LOG": str(traffic_log),
    }
    mocked_routes = [
        {
            "method": "GET",
            "legacy_path": "/api/products",
            "django_replacement": "/api/v1/catalog/products/",
            "replacement_ready": True,
            "notes": "mocked replacement",
        }
    ]

    result = evaluate_api_decommission_readiness(env, routes=mocked_routes)

    assert result["status"] == "blocked_safely"
    assert result["traffic_verification"]["legacy_api_hits"] == 1
