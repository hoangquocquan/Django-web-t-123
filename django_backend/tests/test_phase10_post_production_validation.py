"""Tests for Phase 10.6 post-production validation workflow."""

from scripts.phase10_post_production_validation import evaluate_post_production_validation


def test_post_production_validation_blocks_without_cutover_marker():
    """Validation should keep legacy active before production cutover is proven."""
    result = evaluate_post_production_validation({})

    assert result["status"] == "blocked_safely"
    assert result["legacy_shutdown_recommendation"] == "KEEP_LEGACY_ACTIVE"
    assert result["legacy_shutdown_executed"] is False
    assert result["rollback_capability_removed"] is False


def test_post_production_validation_keeps_legacy_active_when_business_flags_missing():
    """Even with a mocked cutover marker, missing business approvals should block."""
    env = {
        "PHASE10_CUTOVER_COMPLETED": "completed",
        "PHASE10_PRODUCTION_DATABASE_URL": "postgresql://user:secret@localhost:5432/mecprecision_dryrun",
    }

    result = evaluate_post_production_validation(env)

    assert result["status"] == "blocked_safely"
    assert result["legacy_shutdown_recommendation"] == "KEEP_LEGACY_ACTIVE"
    assert result["destructive_cleanup_executed"] is False


def test_post_production_validation_can_allow_phase_11_when_all_checks_are_mocked(monkeypatch):
    """A fully mocked passing post-cutover state can recommend Phase 11."""
    env = {
        "PHASE10_CATALOG_FLOW_VALIDATED": "passed",
        "PHASE10_CRM_FLOW_VALIDATED": "passed",
        "PHASE10_SALES_FLOW_VALIDATED": "passed",
        "PHASE10_CMS_FLOW_VALIDATED": "passed",
        "PHASE10_AUTH_FLOW_VALIDATED": "passed",
        "PHASE10_ERROR_MONITORING_CLEAN": "passed",
        "PHASE10_PERFORMANCE_BASELINE_RECORDED": "passed",
        "PHASE10_ROLLBACK_WINDOW_COMPLETE": "completed",
        "PHASE10_BUSINESS_APPROVAL_RECEIVED": "approved",
    }

    def fake_validation(_env):
        return {
            "status": "passed",
            "errors": [],
            "database": {"connection": {"connection_ok": True}},
            "application": {"api_health": "passed"},
        }

    monkeypatch.setattr(
        "scripts.phase10_post_production_validation.evaluate_post_cutover_validation",
        fake_validation,
    )

    result = evaluate_post_production_validation(env)

    assert result["status"] == "passed"
    assert result["legacy_shutdown_recommendation"] == "ALLOW_PHASE_11"
    assert result["legacy_shutdown_executed"] is False
