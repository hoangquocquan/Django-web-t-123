"""Tests cho cổng kiểm tra shutdown legacy Phase 11."""

from scripts.phase11_legacy_shutdown_readiness import evaluate_shutdown_readiness


def test_phase11_blocks_when_phase10_decision_keeps_legacy_active():
    """Báo cáo hiện tại vẫn yêu cầu giữ legacy, nên shutdown phải bị chặn."""
    result = evaluate_shutdown_readiness({})

    assert result["status"] == "blocked_safely"
    assert result["legacy_shutdown_recommendation"] == "KEEP_LEGACY_ACTIVE"
    assert result["legacy_shutdown_executed"] is False
    assert result["legacy_database_deleted"] is False
    assert result["backups_deleted"] is False


def test_phase11_blocks_when_operational_evidence_is_missing(tmp_path):
    """Có marker kiến trúc nhưng thiếu bằng chứng vận hành thì vẫn chưa được shutdown."""
    decision_report = tmp_path / "decision.md"
    decision_report.write_text("ALLOW_PHASE_11\n", encoding="utf-8")

    result = evaluate_shutdown_readiness({}, decision_report_path=decision_report)

    assert result["status"] == "blocked_safely"
    assert "PHASE11_ZERO_LEGACY_TRAFFIC_CONFIRMED" in " ".join(result["errors"])
    assert result["legacy_code_removed"] is False


def test_phase11_can_be_ready_for_manual_review_when_all_gates_are_mocked(tmp_path):
    """Khi mọi điều kiện được mock là đã đạt, script chỉ cho phép review thủ công."""
    decision_report = tmp_path / "decision.md"
    decision_report.write_text("ALLOW_PHASE_11\n", encoding="utf-8")
    env = {
        "PHASE11_TRAFFIC_MIGRATION_VERIFIED": "verified",
        "PHASE11_ZERO_LEGACY_TRAFFIC_CONFIRMED": "verified",
        "PHASE11_ROLLBACK_WINDOW_CLOSED": "completed",
        "PHASE11_ARCHIVE_RESTORE_VERIFIED": "verified",
        "PHASE11_BUSINESS_OWNER_APPROVED": "approved",
    }

    result = evaluate_shutdown_readiness(env, decision_report_path=decision_report)

    assert result["status"] == "ready_for_manual_shutdown_review"
    assert result["legacy_shutdown_recommendation"] == "ALLOW_MANUAL_SHUTDOWN_REVIEW"
    assert result["legacy_shutdown_executed"] is False
    assert result["traffic_switch_executed"] is False
