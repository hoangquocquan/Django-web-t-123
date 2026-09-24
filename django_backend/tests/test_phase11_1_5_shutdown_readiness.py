"""Tests for Phase 11.1.5 legacy API shutdown readiness approval."""

from scripts.phase11_1_5_shutdown_readiness_check import evaluate_shutdown_readiness


def ready_evidence():
    """Return production-like evidence that allows decommission."""
    return {
        "status": "READY_FOR_DECOMMISSION",
        "legacy_requests": 0,
        "replacement_requests": 100,
        "unknown_clients": 0,
        "safe_to_decommission": True,
        "logs_provided": True,
        "logs_checked": 1,
        "decision": "READY_FOR_DECOMMISSION",
        "errors": [],
    }


def ready_compatibility():
    """Return compatibility status with all replacements ready."""
    return {
        "replacement_ready": True,
        "ready_replacements": 15,
        "not_ready_replacements": 0,
        "errors": [],
    }


def approved_env(rollback_plan):
    """Return full technical, operational and business approval flags."""
    return {
        "PHASE11_1_5_TECHNICAL_APPROVED": "approved",
        "PHASE11_1_5_BUSINESS_APPROVED": "approved",
        "PHASE11_1_5_ROLLBACK_READY": "approved",
        "PHASE11_1_5_ROLLBACK_OWNER": "operations",
        "PHASE11_1_5_ROLLBACK_PLAN": str(rollback_plan),
        "PHASE11_1_5_MAINTENANCE_WINDOW_APPROVED": "approved",
        "PHASE11_1_5_MONITORING_READY": "ready",
        "PHASE11_1_5_SUPPORT_NOTIFIED": "yes",
        "PHASE11_1_5_USER_IMPACT_REVIEWED": "verified",
        "PHASE11_1_5_APPROVAL_ID": "APPROVAL-11.1.5",
    }


def test_missing_evidence_blocks_shutdown():
    """Without production evidence the final decision must keep legacy API active."""
    result = evaluate_shutdown_readiness(env={}, compatibility=ready_compatibility())

    assert result["status"] == "KEEP_LEGACY_API_ACTIVE"
    assert result["ready_for_shutdown"] is False
    assert "Production traffic evidence is not ready for decommission." in result["errors"]
    assert result["legacy_routes_disabled"] is False


def test_missing_approval_blocks_shutdown(tmp_path):
    """Good evidence alone is not enough without business and technical approval."""
    rollback_plan = tmp_path / "rollback.md"
    rollback_plan.write_text("# rollback\n", encoding="utf-8")

    result = evaluate_shutdown_readiness(
        env={"PHASE11_1_5_ROLLBACK_PLAN": str(rollback_plan)},
        evidence=ready_evidence(),
        compatibility=ready_compatibility(),
    )

    assert result["status"] == "KEEP_LEGACY_API_ACTIVE"
    assert "Technical approval is missing." in result["errors"]
    assert "Business approval is missing." in result["errors"]


def test_unknown_client_blocks_shutdown(tmp_path):
    """Unknown clients in evidence must block final shutdown."""
    rollback_plan = tmp_path / "rollback.md"
    rollback_plan.write_text("# rollback\n", encoding="utf-8")
    evidence = ready_evidence()
    evidence["unknown_clients"] = 1

    result = evaluate_shutdown_readiness(
        env=approved_env(rollback_plan),
        evidence=evidence,
        compatibility=ready_compatibility(),
    )

    assert result["status"] == "KEEP_LEGACY_API_ACTIVE"
    assert "Unknown clients must be zero." in result["errors"]


def test_rollback_missing_blocks_shutdown(tmp_path):
    """A rollback owner and rollback plan must exist before shutdown."""
    missing_plan = tmp_path / "missing-rollback.md"
    env = approved_env(missing_plan)
    env["PHASE11_1_5_ROLLBACK_READY"] = "approved"

    result = evaluate_shutdown_readiness(
        env=env,
        evidence=ready_evidence(),
        compatibility=ready_compatibility(),
    )

    assert result["status"] == "KEEP_LEGACY_API_ACTIVE"
    assert any("Rollback plan does not exist" in error for error in result["errors"])


def test_full_approval_is_accepted(tmp_path):
    """Complete evidence and approval should return READY_FOR_LEGACY_API_SHUTDOWN."""
    rollback_plan = tmp_path / "rollback.md"
    rollback_plan.write_text("# rollback\n", encoding="utf-8")

    result = evaluate_shutdown_readiness(
        env=approved_env(rollback_plan),
        evidence=ready_evidence(),
        compatibility=ready_compatibility(),
    )

    assert result["status"] == "READY_FOR_LEGACY_API_SHUTDOWN"
    assert result["ready_for_shutdown"] is True
    assert result["production_routing_changed"] is False
