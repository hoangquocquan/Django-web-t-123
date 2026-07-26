"""Tests for Phase 11.1.5.1 final shutdown readiness validation."""

from scripts.phase11_1_5_1_final_shutdown_readiness import evaluate_final_shutdown_readiness


def complete_evidence():
    """Return production-like evidence that satisfies traffic requirements."""
    return {
        "status": "READY_FOR_DECOMMISSION",
        "legacy_requests": 0,
        "replacement_requests": 2500,
        "unknown_clients": 0,
        "logs_provided": True,
        "logs_checked": 4,
        "safe_to_decommission": True,
        "decision": "READY_FOR_DECOMMISSION",
        "errors": [],
    }


def complete_env(rollback_plan):
    """Return full final approval context."""
    return {
        "PHASE11_1_5_1_TECHNICAL_APPROVAL": "approved",
        "PHASE11_1_5_1_TECHNICAL_NAME": "Lead Architect",
        "PHASE11_1_5_1_TECHNICAL_ROLE": "Architecture Reviewer",
        "PHASE11_1_5_1_BUSINESS_APPROVAL": "approved",
        "PHASE11_1_5_1_BUSINESS_NAME": "Business Owner",
        "PHASE11_1_5_1_BUSINESS_ROLE": "Product Owner",
        "PHASE11_1_5_1_ROLLBACK_READY": "approved",
        "PHASE11_1_5_1_ROLLBACK_OWNER": "Operations",
        "PHASE11_1_5_1_ROLLBACK_CONTACT": "ops@example.com",
        "PHASE11_1_5_1_ROLLBACK_PLAN": str(rollback_plan),
        "PHASE11_1_5_1_MONITORING_READY": "ready",
        "PHASE11_1_5_1_MAINTENANCE_START": "2026-08-01T22:00:00+07:00",
        "PHASE11_1_5_1_MAINTENANCE_END": "2026-08-01T23:00:00+07:00",
        "PHASE11_1_5_1_APPROVAL_ID": "APPROVAL-11.1.5.1",
    }


def test_missing_logs_block_shutdown():
    """Without production logs the validator must keep legacy API active."""
    result = evaluate_final_shutdown_readiness(env={}, evidence=None)

    assert result["status"] == "KEEP_LEGACY_API_ACTIVE"
    assert result["ready_for_shutdown"] is False
    assert "Production logs are missing." in result["errors"]


def test_missing_approval_blocks_shutdown(tmp_path):
    """Complete traffic evidence still needs final approval."""
    rollback_plan = tmp_path / "rollback.md"
    rollback_plan.write_text("# rollback\n", encoding="utf-8")

    result = evaluate_final_shutdown_readiness(
        env={"PHASE11_1_5_1_ROLLBACK_PLAN": str(rollback_plan)},
        evidence=complete_evidence(),
    )

    assert result["status"] == "KEEP_LEGACY_API_ACTIVE"
    assert "Technical approval is missing." in result["errors"]
    assert "Business approval is missing." in result["errors"]


def test_unknown_clients_block_shutdown(tmp_path):
    """Unknown clients must be zero before approval completion."""
    rollback_plan = tmp_path / "rollback.md"
    rollback_plan.write_text("# rollback\n", encoding="utf-8")
    evidence = complete_evidence()
    evidence["unknown_clients"] = 2

    result = evaluate_final_shutdown_readiness(
        env=complete_env(rollback_plan),
        evidence=evidence,
    )

    assert result["status"] == "KEEP_LEGACY_API_ACTIVE"
    assert "Unknown clients must equal zero." in result["errors"]


def test_rollback_missing_blocks_shutdown(tmp_path):
    """Rollback plan and owner evidence are mandatory."""
    missing_plan = tmp_path / "missing-rollback.md"

    result = evaluate_final_shutdown_readiness(
        env=complete_env(missing_plan),
        evidence=complete_evidence(),
    )

    assert result["status"] == "KEEP_LEGACY_API_ACTIVE"
    assert any("Rollback plan does not exist" in error for error in result["errors"])


def test_complete_approval_passes(tmp_path):
    """Complete evidence plus approval returns READY_FOR_LEGACY_API_SHUTDOWN."""
    rollback_plan = tmp_path / "rollback.md"
    rollback_plan.write_text("# rollback\n", encoding="utf-8")

    result = evaluate_final_shutdown_readiness(
        env=complete_env(rollback_plan),
        evidence=complete_evidence(),
    )

    assert result["status"] == "READY_FOR_LEGACY_API_SHUTDOWN"
    assert result["ready_for_shutdown"] is True
    assert result["routing_changed"] is False
