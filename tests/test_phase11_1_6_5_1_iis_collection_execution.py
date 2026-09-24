import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase11_1_6_5_1_collection_validator import REQUIRED_CSV_FIELDS, build_report


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=REQUIRED_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_iis_log(path, endpoint="/api/v1/catalog/products/"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "#Software: Microsoft Internet Information Services 10.0",
                "#Fields: date time c-ip cs-method cs-uri-stem sc-status cs(User-Agent)",
                f"2026-07-20 01:00:00 10.0.0.10 GET {endpoint} 200 DjangoClient",
            ]
        ),
        encoding="utf-8",
    )
    return path


def row(endpoint="/api/v1/catalog/products/", client="10.0.0.10"):
    return {
        "timestamp": "2026-07-20T01:00:00Z",
        "source": "iis",
        "client": client,
        "endpoint": endpoint,
        "status_code": "200",
        "user_agent": "DjangoClient",
    }


def test_missing_iis_logs_blocks_collection(tmp_path):
    write_csv(tmp_path / "iis_api_evidence.csv", [row()])

    result = build_report(
        input_dir=tmp_path,
        output_path=tmp_path / "report.json",
        review_path=tmp_path / "review.md",
        period="2026-07-20 to 2026-07-26",
    )

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert "IIS logs were not found." in result["errors"]


def test_empty_csv_blocks_collection(tmp_path):
    write_iis_log(tmp_path / "iis_logs" / "u_ex260720.log")
    write_csv(tmp_path / "iis_api_evidence.csv", [])

    result = build_report(
        input_dir=tmp_path,
        output_path=tmp_path / "report.json",
        review_path=tmp_path / "review.md",
        period="2026-07-20 to 2026-07-26",
    )

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert "CSV evidence export is empty." in result["errors"]


def test_valid_iis_sample_completes_collection(tmp_path):
    write_iis_log(tmp_path / "iis_logs" / "u_ex260720.log")
    write_csv(tmp_path / "iis_api_evidence.csv", [row(), row(endpoint="/api/v1/sales/quotes/", client="10.0.0.11")])

    result = build_report(
        input_dir=tmp_path,
        output_path=tmp_path / "report.json",
        review_path=tmp_path / "review.md",
        period="2026-07-20 to 2026-07-26",
    )

    assert result["status"] == "COMPLETE_EVIDENCE_PACKAGE"
    assert result["log_files_collected"] == 1
    assert result["django_requests"] == 2
    assert result["legacy_requests"] == 0


def test_legacy_route_detection_blocks_collection(tmp_path):
    write_iis_log(tmp_path / "iis_logs" / "u_ex260720.log", endpoint="/api/products")
    write_csv(tmp_path / "iis_api_evidence.csv", [row(endpoint="/api/products"), row()])

    result = build_report(
        input_dir=tmp_path,
        output_path=tmp_path / "report.json",
        review_path=tmp_path / "review.md",
        period="2026-07-20 to 2026-07-26",
    )

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert result["legacy_requests"] == 1
    assert "Legacy `/api/*` traffic was detected." in result["errors"]


def test_django_route_detection_requires_api_v1(tmp_path):
    write_iis_log(tmp_path / "iis_logs" / "u_ex260720.log", endpoint="/health")
    write_csv(tmp_path / "iis_api_evidence.csv", [row(endpoint="/health")])

    result = build_report(
        input_dir=tmp_path,
        output_path=tmp_path / "report.json",
        review_path=tmp_path / "review.md",
        period="2026-07-20 to 2026-07-26",
    )

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert result["django_requests"] == 0
    assert "Django `/api/v1/*` traffic was not confirmed." in result["errors"]
