"""Tests for Phase 10.4 production cutover readiness gate."""

import hashlib

from scripts.phase10_cutover_readiness import (
    evaluate_cutover_readiness,
    validate_production_database_url,
)


def test_cutover_readiness_blocks_without_required_approvals():
    """Cutover must remain blocked when approvals and backup are missing."""
    result = evaluate_cutover_readiness({})

    assert result["status"] == "blocked"
    assert result["production_cutover_executed"] is False
    assert result["production_database_switched"] is False
    assert result["errors"]


def test_cutover_readiness_rejects_non_production_database_name():
    """Production cutover must not target dry-run/test database names."""
    validation = validate_production_database_url(
        "postgresql://user:secret@localhost:5432/mecprecision_dryrun"
    )

    assert validation["errors"]
    assert "secret" not in validation["masked_database_url"]


def test_cutover_readiness_accepts_complete_mocked_inputs(tmp_path):
    """A fully configured dry check can become ready without executing cutover."""
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
        "PHASE10_CUTOVER_APPROVAL_ID": "APPROVAL-10.4",
    }

    result = evaluate_cutover_readiness(env)

    assert result["status"] == "ready"
    assert result["ready_for_cutover"] is True
    assert result["production_cutover_executed"] is False
    assert result["backup"]["actual_sha256"] == checksum


def test_cutover_readiness_detects_backup_checksum_mismatch(tmp_path):
    """A wrong backup checksum must block cutover readiness."""
    backup = tmp_path / "legacy-final.sqlite"
    backup.write_bytes(b"backup")
    env = {
        "PHASE10_MAINTENANCE_WINDOW_APPROVED": "approved",
        "PHASE10_LEGACY_WRITE_FREEZE_APPROVED": "approved",
        "PHASE10_ROLLBACK_APPROVED": "approved",
        "PHASE10_FINAL_BACKUP_VERIFIED": "approved",
        "PHASE10_PRODUCTION_DATABASE_URL": "postgresql://prod_user:secret@db:5432/mecprecision",
        "PHASE10_FINAL_BACKUP_PATH": str(backup),
        "PHASE10_FINAL_BACKUP_SHA256": "wrong",
        "PHASE10_ROLLBACK_OWNER": "database-owner",
        "PHASE10_CUTOVER_APPROVAL_ID": "APPROVAL-10.4",
    }

    result = evaluate_cutover_readiness(env)

    assert result["status"] == "blocked"
    assert "checksum" in " ".join(result["errors"]).lower()
