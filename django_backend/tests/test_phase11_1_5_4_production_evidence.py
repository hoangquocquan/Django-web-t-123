"""Tests for Phase 11.1.5.4 real production evidence validation."""

from scripts.phase11_1_5_4_client_dependency_validator import validate_client_dependencies
from scripts.phase11_1_5_4_production_evidence_loader import collect_production_evidence


def test_empty_data_blocked(tmp_path):
    """No production data inputs must keep evidence incomplete."""
    report = tmp_path / "report.json"
    result = collect_production_evidence([], report_path=report)

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert result["legacy_requests"] == 0
    assert result["django_requests"] == 0
    assert report.exists()


def test_legacy_traffic_detected(tmp_path):
    """Any legacy `/api/...` traffic must block shutdown readiness."""
    source = tmp_path / "gateway.csv"
    source.write_text(
        "timestamp,client,endpoint,status_code,request_count\n"
        "2026-08-01T10:00:00+07:00,partner,/api/products,200,5\n",
        encoding="utf-8",
    )

    result = collect_production_evidence([str(source)], report_path=tmp_path / "report.json")

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert result["legacy_requests"] == 5
    assert "Legacy API traffic was detected." in result["errors"]


def test_zero_legacy_traffic_accepted(tmp_path):
    """Valid production data with only Django traffic can complete traffic evidence."""
    source = tmp_path / "gateway.jsonl"
    source.write_text(
        '{"timestamp":"2026-08-01T10:00:00+07:00","client":"frontend","endpoint":"/api/v1/public/home/","status_code":200,"request_count":100}\n'
        '{"timestamp":"2026-08-01T10:05:00+07:00","client":"admin","endpoint":"/api/v1/catalog/products/","status_code":200,"request_count":30}\n',
        encoding="utf-8",
    )

    result = collect_production_evidence([str(source)], report_path=tmp_path / "report.json")

    assert result["status"] == "COMPLETE_EVIDENCE_PACKAGE"
    assert result["legacy_requests"] == 0
    assert result["django_requests"] == 130
    assert result["unknown_clients"] == 0


def test_unknown_client_detected(tmp_path):
    """Legacy hits without client identity must be counted as unknown clients."""
    source = tmp_path / "access.log"
    source.write_text("GET /api/contact 200\n", encoding="utf-8")

    result = collect_production_evidence([str(source)], report_path=tmp_path / "report.json")

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert result["unknown_clients"] == 1
    assert "Unknown clients were detected." in result["errors"]


def test_valid_production_package_accepted(tmp_path):
    """Traffic evidence plus a completed client matrix can be valid."""
    traffic = tmp_path / "gateway.csv"
    traffic.write_text(
        "timestamp,client,endpoint,status_code,request_count\n"
        "2026-08-01T10:00:00+07:00,frontend,/api/v1/public/home/,200,100\n",
        encoding="utf-8",
    )
    matrix = tmp_path / "clients.csv"
    matrix.write_text(
        "client,owner,legacy_api_usage,replacement_api,migration_date,confirmation\n"
        "Frontend,web-owner,0,/api/v1/public/home/,2026-08-01,confirmed\n",
        encoding="utf-8",
    )

    traffic_result = collect_production_evidence([str(traffic)], report_path=tmp_path / "report.json")
    client_result = validate_client_dependencies(matrix)

    assert traffic_result["status"] == "COMPLETE_EVIDENCE_PACKAGE"
    assert client_result["status"] == "CLIENTS_READY"
