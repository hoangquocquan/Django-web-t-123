"""Tests for Phase 11.1.3 controlled legacy API decommission."""

from scripts.phase11_1_3_api_decommission_gate import (
    APPROVAL_CONFIRMATION_TEXT,
    evaluate_decommission_gate,
)
from scripts.phase11_1_3_disable_legacy_api import build_disable_plan, run_disable_workflow


def clean_traffic_result():
    """Return a mocked production traffic result with no legacy API usage."""
    return {
        "status": "passed",
        "legacy_requests": 0,
        "replacement_requests": 5,
        "unknown_clients": 0,
        "logs_provided": True,
        "logs_checked": 1,
        "safe_to_decommission": True,
        "decision": "READY_FOR_DECOMMISSION",
        "sources": [],
        "errors": [],
    }


def approved_env(rollback_plan):
    """Return a complete approval environment for positive-path tests."""
    return {
        "PHASE11_1_3_APPROVAL": "approved",
        "PHASE11_1_3_APPROVAL_ID": "ARCH-APPROVAL-11.1.3",
        "PHASE11_1_3_OPERATOR_CONFIRMATION": APPROVAL_CONFIRMATION_TEXT,
        "PHASE11_1_3_ROLLBACK_READY": "approved",
        "PHASE11_1_3_ROLLBACK_OWNER": "operations",
        "PHASE11_1_3_ROLLBACK_PLAN": str(rollback_plan),
    }


def test_gate_blocks_safely_without_production_evidence():
    """Default local execution must not disable legacy routes."""
    result = evaluate_decommission_gate(env={}, traffic_result=None)

    assert result["status"] == "BLOCKED_SAFELY"
    assert result["decision"] == "KEEP_LEGACY_API_ACTIVE"
    assert result["legacy_routes_disabled"] is False
    assert result["destructive_actions_executed"] is False


def test_gate_blocks_when_approval_is_missing(tmp_path):
    """Clean traffic alone is not enough without approval and rollback owner."""
    rollback_plan = tmp_path / "rollback.md"
    rollback_plan.write_text("# rollback\n", encoding="utf-8")

    result = evaluate_decommission_gate(
        env={"PHASE11_1_3_ROLLBACK_PLAN": str(rollback_plan)},
        traffic_result=clean_traffic_result(),
    )

    assert result["status"] == "BLOCKED_SAFELY"
    assert result["safe_to_execute"] is False
    assert any("Missing approval" in error for error in result["errors"])


def test_gate_blocks_when_traffic_is_not_zero(tmp_path):
    """Any remaining legacy request must block decommission."""
    rollback_plan = tmp_path / "rollback.md"
    rollback_plan.write_text("# rollback\n", encoding="utf-8")
    traffic = clean_traffic_result()
    traffic["legacy_requests"] = 1
    traffic["safe_to_decommission"] = False

    result = evaluate_decommission_gate(
        env=approved_env(rollback_plan),
        traffic_result=traffic,
    )

    assert result["status"] == "BLOCKED_SAFELY"
    assert "Legacy API traffic is still present." in result["errors"]


def test_gate_allows_manual_execution_when_every_condition_passes(tmp_path):
    """With approval, rollback and clean traffic, the gate allows manual execution."""
    rollback_plan = tmp_path / "rollback.md"
    rollback_plan.write_text("# rollback\n", encoding="utf-8")

    result = evaluate_decommission_gate(
        env=approved_env(rollback_plan),
        traffic_result=clean_traffic_result(),
    )

    assert result["status"] == "READY_FOR_DECOMMISSION_EXECUTION"
    assert result["safe_to_execute"] is True
    assert result["legacy_routes_disabled"] is False


def test_disable_workflow_blocks_without_gate_approval():
    """The disable workflow must not apply any route change while gate is blocked."""
    result = run_disable_workflow(env={}, traffic_result=clean_traffic_result())

    assert result["status"] == "BLOCKED_SAFELY"
    assert result["decision"] == "NO_ROUTE_CHANGE_APPLIED"
    assert result["proxy_changes_applied"] is False
    assert result["application_code_changed"] is False


def test_disable_workflow_returns_manual_plan_after_gate_passes(tmp_path):
    """A passed gate should produce a manual plan, not mutate files automatically."""
    rollback_plan = tmp_path / "rollback.md"
    rollback_plan.write_text("# rollback\n", encoding="utf-8")

    result = run_disable_workflow(
        env=approved_env(rollback_plan),
        traffic_result=clean_traffic_result(),
    )

    assert result["status"] == "READY_FOR_MANUAL_DISABLE"
    assert result["legacy_routes_disabled"] is False
    assert result["planned_actions"]


def test_disable_plan_maps_legacy_routes_to_api_v1_replacements():
    """Every planned disable action should keep its Django replacement visible."""
    plan = build_disable_plan()

    assert plan
    assert any(item["legacy_route"] == "/api/contact" for item in plan)
    assert all(item["replacement_route"].startswith("/api/v1/") for item in plan)


def test_django_replacement_api_remains_available(client, legacy_db):
    """The new Django API namespace must stay available during decommission planning."""
    result = run_disable_workflow(env={})
    response = client.get("/api/v1/health/")

    assert result["api_v1_unaffected"] is True
    assert response.status_code == 200
