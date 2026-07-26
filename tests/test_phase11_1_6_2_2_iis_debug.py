import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase11_1_6_2_real_production_evidence import (
    read_records,
    validate_real_production_evidence,
)


def write_iis_log(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def test_valid_iis_w3c_sample_detects_api_and_api_v1(tmp_path):
    write_iis_log(
        tmp_path / "u_ex260726.log",
        [
            "#Software: Microsoft Internet Information Services 10.0",
            "#Fields: date time c-ip cs-method cs-uri-stem sc-status cs(User-Agent)",
            "2026-07-26 01:00:00 10.0.0.10 GET /api/products 200 LegacyClient",
            "2026-07-26 01:01:00 10.0.0.11 GET /api/v1/catalog/products/ 200 DjangoClient",
        ],
    )

    result = validate_real_production_evidence(input_dir=tmp_path, output_path=tmp_path / "report.json")

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert result["legacy_requests"] == 1
    assert result["django_requests"] == 1
    assert "Legacy `/api/*` traffic was detected." in result["errors"]


def test_empty_iis_file_is_blocked(tmp_path):
    write_iis_log(tmp_path / "empty.log", [])

    result = validate_real_production_evidence(input_dir=tmp_path, output_path=tmp_path / "report.json")

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert "No evidence records were found." in result["errors"]


def test_missing_uri_field_does_not_crash_and_blocks(tmp_path):
    path = write_iis_log(
        tmp_path / "missing_uri.log",
        [
            "#Fields: date time c-ip sc-status cs(User-Agent)",
            "2026-07-26 01:00:00 10.0.0.10 200 MissingUriClient",
        ],
    )

    records = read_records(path)
    result = validate_real_production_evidence(input_dir=tmp_path, output_path=tmp_path / "report.json")

    assert len(records) == 1
    assert records[0]["paths"] == []
    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert "Django `/api/v1/*` traffic was not confirmed." in result["errors"]


def test_api_v1_only_iis_sample_can_complete_evidence(tmp_path):
    write_iis_log(
        tmp_path / "api_v1_only.log",
        [
            "#Fields: date time c-ip cs-method cs-uri-stem sc-status cs(User-Agent)",
            "2026-07-26 01:00:00 10.0.0.11 GET /api/v1/catalog/products/ 200 DjangoClient",
            "2026-07-26 01:01:00 10.0.0.12 POST /api/v1/sales/quotes/ 201 DjangoClient",
        ],
    )

    result = validate_real_production_evidence(input_dir=tmp_path, output_path=tmp_path / "report.json")

    assert result["status"] == "COMPLETE_EVIDENCE_PACKAGE"
    assert result["legacy_requests"] == 0
    assert result["django_requests"] == 2
    assert result["unknown_clients"] == 0


def test_powershell_export_handles_valid_iis_sample(tmp_path):
    log_root = tmp_path / "W3SVC1"
    output_path = tmp_path / "iis_api_evidence.csv"
    write_iis_log(
        log_root / "u_ex260726.log",
        [
            "#Fields: date time c-ip cs-method cs-uri-stem sc-status cs(User-Agent)",
            "2026-07-26 01:00:00 10.0.0.10 GET /api/products 200 LegacyClient",
            "2026-07-26 01:01:00 10.0.0.11 GET /api/v1/catalog/products/ 200 DjangoClient",
        ],
    )

    completed = subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(PROJECT_ROOT / "scripts" / "windows" / "export_iis_api_evidence.ps1"),
            "-LogRoot",
            str(log_root),
            "-OutputPath",
            str(output_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8-sig")
    assert "/api/products" in content
    assert "/api/v1/catalog/products/" in content
