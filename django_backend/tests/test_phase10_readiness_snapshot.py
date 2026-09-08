"""Tests for Phase 10 read-only migration readiness snapshot tooling."""

import pytest

from scripts.phase10_readiness_snapshot import EXPECTED_TABLES, snapshot_database


@pytest.mark.legacy_artifact
def test_phase10_snapshot_reads_legacy_database_without_mutation(
    legacy_artifact_path,
):
    """The snapshot script must read expected tables and keep SQLite unchanged."""
    snapshot = snapshot_database(legacy_artifact_path)

    assert snapshot["database_size_unchanged"] is True
    assert snapshot["expected_table_count"] == len(EXPECTED_TABLES)
    assert snapshot["found_table_count"] == len(EXPECTED_TABLES)
    assert snapshot["missing_tables"] == []
    assert snapshot["row_counts"]["products"] >= 0
    assert snapshot["phase10_gate"]["legacy_readonly_snapshot"] is True
    assert snapshot["phase10_gate"]["production_migration_executed"] is False
