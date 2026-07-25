"""Tests for Phase 10.2 dry-run migration safety gate."""

from scripts.phase10_dry_run_migration import (
    evaluate_dry_run,
    is_safe_test_database_url,
    mask_database_url,
    map_sqlite_type_to_postgres,
    target_columns_for_table,
)
from scripts.check_phase10_postgres_connection import (
    evaluate_postgres_environment,
    has_forbidden_database_name,
    validate_dryrun_database_url,
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


def test_dry_run_gate_rejects_production_marker_even_when_dryrun_exists():
    """A database name cannot combine a safe marker with a production marker."""
    result = evaluate_dry_run(
        "postgresql://user:pass@localhost/mecprecision_prod_dryrun"
    )

    assert result["status"] == "blocked"
    assert result["dry_run_allowed"] is False
    assert result["environment_validation"]["has_forbidden_database_name"] is True


def test_dry_run_report_masks_credentials():
    """Reports must not expose database passwords."""
    masked = mask_database_url("postgresql://user:secret-password@localhost:5432/mecprecision_test")

    assert "secret-password" not in masked
    assert "user:***@" in masked


def test_postgres_environment_validator_reports_missing_url_without_connection(monkeypatch):
    """Missing URL should be a safe blocked state and should not touch PostgreSQL."""
    monkeypatch.delenv("PHASE10_DRY_RUN_DATABASE_URL", raising=False)

    result = evaluate_postgres_environment()

    assert result["status"] == "not_configured"
    assert result["production_touched"] is False
    assert result["connection"]["connection_checked"] is False


def test_postgres_environment_validator_rejects_production_database_name():
    """The validator must refuse production-like PostgreSQL database names."""
    database_url = "postgresql://user:pass@localhost:5432/mecprecision_prod"
    validation = validate_dryrun_database_url(database_url)

    assert has_forbidden_database_name(database_url)
    assert validation["has_forbidden_database_name"] is True
    assert validation["errors"]


def test_postgres_environment_validator_rejects_invalid_scheme():
    """The dry-run validator should accept only PostgreSQL URL schemes."""
    validation = validate_dryrun_database_url(
        "sqlite:///backend/database/mecprecision.sqlite"
    )

    assert validation["is_postgresql_url"] is False
    assert "postgres/postgresql URL scheme" in validation["errors"][0]


def test_dry_run_type_mapping_for_postgresql_target_schema():
    """SQLite column types should map to safe PostgreSQL dry-run types."""
    assert map_sqlite_type_to_postgres("INTEGER") == "BIGINT"
    assert map_sqlite_type_to_postgres("REAL") == "NUMERIC"
    assert map_sqlite_type_to_postgres("TEXT") == "TEXT"


def test_dry_run_link_tables_use_surrogate_id_for_target_schema():
    """Approved PostgreSQL design uses surrogate IDs for catalog link tables."""
    columns = [
        {"name": "product_id", "type": "INTEGER", "notnull": True, "pk": 1},
        {"name": "material_id", "type": "INTEGER", "notnull": True, "pk": 2},
    ]

    target_columns = target_columns_for_table(columns, "product_materials")

    assert target_columns[0]["name"] == "id"
    assert target_columns[0]["primary_key"] is True
    assert target_columns[1]["name"] == "product_id"
