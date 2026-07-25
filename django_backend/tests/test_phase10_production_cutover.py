"""Tests for Phase 10.5 production cutover workflow gates."""

import hashlib

from scripts.phase10_post_cutover_validation import evaluate_post_cutover_validation
from scripts.phase10_production_cutover import (
    EXPECTED_OPERATOR_CONFIRMATION,
    evaluate_cutover_execution,
)


def test_production_cutover_blocks_without_operator_controls():
    """Execution must remain safely blocked when approvals are missing."""
    result = evaluate_cutover_execution({})

    assert result["status"] == "blocked_safely"
    assert result["production_cutover_executed"] is False
    assert result["destructive_actions_executed"] is False
    assert result["traffic_switched"] is False


def test_production_cutover_allows_only_manual_steps_when_controls_are_complete(tmp_path):
    """Complete mocked controls allow manual cutover but still execute nothing."""
    backup = tmp_path / "legacy-final.sqlite"
    backup.write_bytes(b"backup")
    checksum = hashlib.sha256(b"backup").hexdigest()
    env = {
        "PHASE10_MAINTENANCE_WINDOW_APPROVED": "approved",
        "PHASE10_LEGACY_WRITE_FREEZE_APPROVED": "approved",
        "PHASE10_ROLLBACK_APPROVED": "approved",
        "PHASE10_FINAL_BACKUP_VERIFIED": "approved",
        "PHASE10_PRODUCTION_DATABASE_URL": "postgresql://prod_user:secret@db:5432/mecprecision",
        "PHASE10_FINAL_BACKUP_PATH": str(backup),
        "PHASE10_FINAL_BACKUP_SHA256": checksum,
        "PHASE10_ROLLBACK_OWNER": "database-owner",
        "PHASE10_CUTOVER_APPROVAL_ID": "APPROVAL-10.5",
        "PHASE10_OPERATOR_CONFIRMATION": EXPECTED_OPERATOR_CONFIRMATION,
        "PHASE10_EXECUTE_CUTOVER_APPROVED": "approved",
    }

    result = evaluate_cutover_execution(env)

    assert result["status"] == "ready_for_manual_cutover"
    assert result["manual_cutover_allowed"] is True
    assert result["production_cutover_executed"] is False
    assert result["database_migration_executed"] is False


def test_post_cutover_validation_blocks_before_cutover_marker():
    """Post-cutover validation should not query production before cutover is marked."""
    result = evaluate_post_cutover_validation({})

    assert result["status"] == "blocked_safely"
    assert result["post_cutover_validation_executed"] is False
    assert result["errors"]


def test_post_cutover_validation_rejects_dryrun_database_even_after_marker():
    """Production validation must reject dry-run database names."""
    env = {
        "PHASE10_CUTOVER_COMPLETED": "completed",
        "PHASE10_PRODUCTION_DATABASE_URL": "postgresql://user:secret@localhost:5432/mecprecision_dryrun",
    }

    result = evaluate_post_cutover_validation(env)

    assert result["status"] == "blocked_safely"
    assert "non-production" in " ".join(result["errors"]).lower()
