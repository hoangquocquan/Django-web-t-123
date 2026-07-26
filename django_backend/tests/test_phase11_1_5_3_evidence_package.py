"""Tests for Phase 11.1.5.3 production evidence package validation."""

from pathlib import Path

from scripts.phase11_1_5_3_evidence_package_validator import REQUIRED_FILES, validate_package


def write_complete_package(root):
    """Create a complete evidence package in a temporary directory."""
    for relative_path in REQUIRED_FILES.values():
        path = Path(root) / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".csv":
            if "TRAFFIC" in path.name:
                path.write_text(
                    "verification_start,verification_end,log_source,total_requests,legacy_api_requests,django_api_v1_requests,unknown_clients,evidence_owner,evidence_timestamp\n"
                    "2026-08-01,2026-08-30,nginx,10000,0,4000,0,ops,2026-08-31T10:00:00+07:00\n",
                    encoding="utf-8",
                )
            else:
                path.write_text(
                    "client,owner,legacy_api_usage,replacement_api,migration_date,confirmation\n"
                    "Frontend,web-owner,0,/api/v1/public/home/,2026-08-01,confirmed\n",
                    encoding="utf-8",
                )
        else:
            path.write_text(
                "# Completed Evidence\n\n"
                "Name: Approved Owner\n"
                "Role: Owner\n"
                "Date: 2026-08-31\n"
                "Confirmation: confirmed\n",
                encoding="utf-8",
            )


def test_missing_evidence_blocked(tmp_path):
    """A missing package root must be incomplete."""
    result = validate_package(tmp_path / "missing")

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert result["complete"] is False
    assert result["legacy_routes_disabled"] is False


def test_missing_approval_blocked(tmp_path):
    """Missing approval files must block package completeness."""
    write_complete_package(tmp_path)
    (tmp_path / "approvals" / "TECHNICAL_APPROVAL.md").unlink()

    result = validate_package(tmp_path)

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert any("TECHNICAL_APPROVAL.md" in error for error in result["missing_requirements"])


def test_missing_client_confirmation_blocked(tmp_path):
    """Missing client confirmation must block package completeness."""
    write_complete_package(tmp_path)
    (tmp_path / "clients" / "CLIENT_DEPENDENCY_MATRIX.csv").write_text(
        "client,owner,legacy_api_usage,replacement_api,migration_date,confirmation\n"
        "Frontend,PENDING,PENDING,PENDING,PENDING,PENDING\n",
        encoding="utf-8",
    )

    result = validate_package(tmp_path)

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert any("CLIENT_DEPENDENCY_MATRIX.csv" in error for error in result["missing_requirements"])


def test_complete_package_accepted(tmp_path):
    """A package with all files filled in can be complete."""
    write_complete_package(tmp_path)

    result = validate_package(tmp_path)

    assert result["status"] == "COMPLETE_EVIDENCE_PACKAGE"
    assert result["complete"] is True
    assert result["routes_changed"] is False
