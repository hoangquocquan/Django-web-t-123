"""Tests for Phase 10.3 data reconciliation helpers."""

from decimal import Decimal

from scripts.phase10_data_reconciliation import (
    checksum_rows,
    is_sensitive_column,
    normalize_value,
)


def test_reconciliation_masks_sensitive_columns_in_checksums():
    """Changing token/password values should not change public checksum output."""
    columns = ["id", "email", "password_hash", "reset_token"]
    first_rows = [(1, "admin@example.com", "secret-1", "token-1")]
    second_rows = [(1, "admin@example.com", "secret-2", "token-2")]

    assert checksum_rows(columns, first_rows) == checksum_rows(columns, second_rows)


def test_reconciliation_detects_non_sensitive_value_changes():
    """Business value changes should change the checksum."""
    columns = ["id", "name"]

    assert checksum_rows(columns, [(1, "A")]) != checksum_rows(columns, [(1, "B")])


def test_reconciliation_normalizes_numeric_values_between_sqlite_and_postgres():
    """SQLite floats and PostgreSQL decimals should compare consistently."""
    assert normalize_value(Decimal("0.0")) == "0"
    assert normalize_value(0.0) == "0"
    assert normalize_value(Decimal("12.3400")) == "12.34"


def test_reconciliation_identifies_sensitive_column_names():
    """Security-related columns should be excluded from value-level reports."""
    assert is_sensitive_column("password_hash")
    assert is_sensitive_column("session_id")
    assert is_sensitive_column("reset_token")
    assert not is_sensitive_column("email")
