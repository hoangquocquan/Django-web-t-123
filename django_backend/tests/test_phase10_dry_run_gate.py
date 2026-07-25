"""Tests for Phase 10.2 dry-run migration safety gate."""

from scripts.phase10_dry_run_migration import (
    evaluate_dry_run,
    is_safe_test_database_url,
    mask_database_url,
)


def test_dry_run_gate_blocks_missing_target_database(monkeypatch):
    """Without a PostgreSQL test URL the dry run must stay blocked."""
    monkeypatch.delenv("PHASE10_DRY_RUN_DATABASE_URL", raising=False)

    result = evaluate_dry_run()

    assert result["status"] == "blocked"
    assert result["dry_run_allowed"] is False
    assert result["execution"]["production_touched"] is False
    assert result["legacy_snapshot"]["found_table_count"] == 27


def test_dry_run_gate_accepts_only_safe_test_database_names():
    """The gate should reject production-looking target database names."""
    assert is_safe_test_database_url("postgresql://user:pass@localhost/mecprecision_dryrun")
    assert is_safe_test_database_url("postgresql://user:pass@localhost/mecprecision_test")
    assert not is_safe_test_database_url("postgresql://user:pass@localhost/mecprecision_prod")


def test_dry_run_report_masks_credentials():
    """Reports must not expose database passwords."""
    masked = mask_database_url("postgresql://user:secret-password@localhost:5432/mecprecision_test")

    assert "secret-password" not in masked
    assert "user:***@" in masked
