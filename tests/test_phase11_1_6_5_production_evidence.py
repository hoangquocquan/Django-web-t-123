import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase11_1_6_5_production_evidence_validator import (
    REQUIRED_CSV_FIELDS,
    validate_production_evidence_package,
)


def write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fieldnames or REQUIRED_CSV_FIELDS
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_iis_log(path, rows=None):
    lines = [
        "#Software: Microsoft Internet Information Services 10.0",
        "#Fields: date time c-ip cs-method cs-uri-stem sc-status cs(User-Agent)",
    ]
    lines.extend(rows or ["2026-07-20 01:00:00 10.0.0.10 GET /api/v1/catalog/products/ 200 DjangoClient"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_metadata(input_dir, environment="production", simulation=False):
    metadata = {
        "server": "IIS-PROD-01",
        "environment": environment,
        "simulation": simulation,
        "source": "iis_w3c_logs_and_csv",
        "collection_period": "2026-07-20 to 2026-07-26",
        "approved_by": "ops-owner",
        "iis_site": "MECPrecision-Web",
        "site_id": "1",
    }
    path = Path(input_dir).parent / "handover" / "collection_metadata.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata), encoding="utf-8")
    return path


def valid_django_row(client="client-a", endpoint="/api/v1/catalog/products/"):
    return {
        "timestamp": "2026-07-20T01:00:00Z",
        "source": "iis",
        "client": client,
        "endpoint": endpoint,
        "status_code": "200",
        "user_agent": "DjangoClient",
    }


def test_empty_evidence_blocked(tmp_path):
    result = validate_production_evidence_package(
        input_dir=tmp_path,
        output_path=tmp_path / "report.json",
        review_path=tmp_path / "review.md",
    )

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert "No production evidence files were found." in result["errors"]
    assert "CSV export does not exist:" in " ".join(result["errors"])


def test_invalid_csv_blocked(tmp_path):
    write_iis_log(tmp_path / "iis_logs" / "u_ex260720.log")
    write_csv(
        tmp_path / "iis_api_evidence.csv",
        [{"timestamp": "2026-07-20T01:00:00Z", "endpoint": "/api/v1/catalog/products/"}],
        fieldnames=["timestamp", "endpoint"],
    )

    result = validate_production_evidence_package(
        input_dir=tmp_path,
        output_path=tmp_path / "report.json",
        review_path=tmp_path / "review.md",
    )

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert any("CSV export is missing required fields" in error for error in result["errors"])


def test_legacy_traffic_detected(tmp_path):
    write_iis_log(
        tmp_path / "iis_logs" / "u_ex260720.log",
        rows=[
            "2026-07-20 01:00:00 10.0.0.10 GET /api/products 200 LegacyClient",
            "2026-07-20 01:01:00 10.0.0.11 GET /api/v1/catalog/products/ 200 DjangoClient",
        ],
    )
    write_csv(
        tmp_path / "iis_api_evidence.csv",
        [
            valid_django_row(endpoint="/api/products"),
            valid_django_row(endpoint="/api/v1/catalog/products/"),
        ],
    )

    result = validate_production_evidence_package(
        input_dir=tmp_path,
        output_path=tmp_path / "report.json",
        review_path=tmp_path / "review.md",
    )

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert result["legacy_requests"] >= 1
    assert "Legacy `/api/*` traffic was detected." in result["errors"]


def test_django_traffic_detected_but_missing_period_blocked(tmp_path):
    write_iis_log(
        tmp_path / "iis_logs" / "u_ex260720.log",
        rows=["10.0.0.10 GET /api/v1/catalog/products/ 200 DjangoClient"],
    ).write_text(
        "\n".join(
            [
                "#Fields: c-ip cs-method cs-uri-stem sc-status cs(User-Agent)",
                "10.0.0.10 GET /api/v1/catalog/products/ 200 DjangoClient",
            ]
        ),
        encoding="utf-8",
    )
    write_csv(
        tmp_path / "iis_api_evidence.csv",
        [
            {
                "timestamp": "",
                "source": "iis",
                "client": "client-a",
                "endpoint": "/api/v1/catalog/products/",
                "status_code": "200",
                "user_agent": "DjangoClient",
            }
        ],
    )

    result = validate_production_evidence_package(
        input_dir=tmp_path,
        output_path=tmp_path / "report.json",
        review_path=tmp_path / "review.md",
    )

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert result["django_requests"] >= 1
    assert "Collection period is not provided." in result["errors"]


def test_complete_package_accepted(tmp_path):
    input_dir = tmp_path / "input"
    write_metadata(input_dir)
    write_iis_log(input_dir / "iis_logs" / "u_ex260720.log")
    write_csv(
        input_dir / "iis_api_evidence.csv",
        [
            valid_django_row(client="client-a", endpoint="/api/v1/catalog/products/"),
            valid_django_row(client="client-b", endpoint="/api/v1/sales/quotes/"),
        ],
    )

    result = validate_production_evidence_package(
        input_dir=input_dir,
        output_path=tmp_path / "report.json",
        review_path=tmp_path / "review.md",
        period="2026-07-20 to 2026-07-26",
    )

    assert result["status"] == "COMPLETE_EVIDENCE_PACKAGE"
    assert result["ready_for_shutdown"] is True
    assert result["legacy_requests"] == 0
    assert result["django_requests"] >= 2
    assert result["unknown_clients"] == 0
    assert (tmp_path / "review.md").exists()
