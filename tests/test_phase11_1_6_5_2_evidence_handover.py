import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase11_1_6_5_2_evidence_acceptance_validator import REQUIRED_CSV_FIELDS, evaluate_acceptance


def write_metadata(package_dir, overrides=None):
    data = {
        "server": "prod-web-01",
        "environment": "production",
        "iis_site": "MecPrecision",
        "site_id": "1",
        "collection_start": "2026-07-01",
        "collection_end": "2026-07-30",
        "operator": "IIS Admin",
        "reviewer": "Architecture Reviewer",
        "notes": "Sanitized evidence package.",
    }
    data.update(overrides or {})
    path = Path(package_dir) / "handover" / "collection_metadata.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def write_iis_log(package_dir, fields=None, row_endpoint="/api/v1/catalog/products/"):
    fields = fields or ["date", "time", "c-ip", "cs-method", "cs-uri-stem", "sc-status", "cs(User-Agent)"]
    values = {
        "date": "2026-07-20",
        "time": "01:00:00",
        "c-ip": "10.0.0.10",
        "cs-method": "GET",
        "cs-uri-stem": row_endpoint,
        "sc-status": "200",
        "cs(User-Agent)": "DjangoClient",
    }
    path = Path(package_dir) / "input" / "iis_logs" / "u_ex260720.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "#Software: Microsoft Internet Information Services 10.0",
                "#Fields: " + " ".join(fields),
                " ".join(values.get(field, "-") for field in fields),
            ]
        ),
        encoding="utf-8",
    )
    return path


def write_csv(package_dir, rows):
    path = Path(package_dir) / "input" / "iis_api_evidence.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=REQUIRED_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def csv_row(endpoint="/api/v1/catalog/products/", client="10.0.0.10"):
    return {
        "timestamp": "2026-07-20T01:00:00Z",
        "source": "iis",
        "client": client,
        "endpoint": endpoint,
        "status_code": "200",
        "user_agent": "DjangoClient",
    }


def run_validator(package_dir):
    return evaluate_acceptance(
        package_dir=package_dir,
        output_path=Path(package_dir) / "handover" / "status.json",
        review_path=Path(package_dir) / "handover" / "review.md",
    )


def test_missing_logs_rejected(tmp_path):
    write_metadata(tmp_path)
    write_csv(tmp_path, [csv_row()])

    result = run_validator(tmp_path)

    assert result["status"] == "EVIDENCE_REJECTED"
    assert "IIS logs do not exist." in result["errors"]


def test_missing_metadata_rejected(tmp_path):
    write_iis_log(tmp_path)
    write_csv(tmp_path, [csv_row()])

    result = run_validator(tmp_path)

    assert result["status"] == "EVIDENCE_REJECTED"
    assert any("Collection metadata does not exist" in error for error in result["errors"])


def test_invalid_package_rejected(tmp_path):
    write_metadata(tmp_path, {"collection_start": "PENDING"})
    write_iis_log(tmp_path, fields=["date", "time", "c-ip", "sc-status"])
    write_csv(tmp_path, [])

    result = run_validator(tmp_path)

    assert result["status"] == "EVIDENCE_REJECTED"
    assert "Metadata field is pending: collection_start." in result["errors"]
    assert any("IIS log is missing required fields" in error for error in result["errors"])
    assert "CSV evidence is empty." in result["errors"]


def test_legacy_traffic_rejected(tmp_path):
    write_metadata(tmp_path)
    write_iis_log(tmp_path, row_endpoint="/api/products")
    write_csv(tmp_path, [csv_row(endpoint="/api/products"), csv_row()])

    result = run_validator(tmp_path)

    assert result["status"] == "EVIDENCE_REJECTED"
    assert result["traffic"]["legacy_requests"] == 1
    assert "Legacy `/api/*` traffic was detected." in result["errors"]


def test_valid_package_accepted(tmp_path):
    write_metadata(tmp_path)
    write_iis_log(tmp_path)
    write_csv(tmp_path, [csv_row(), csv_row(endpoint="/api/v1/sales/quotes/", client="10.0.0.11")])

    result = run_validator(tmp_path)

    assert result["status"] == "EVIDENCE_ACCEPTED"
    assert result["metadata_valid"] is True
    assert result["iis_logs"]["count"] == 1
    assert result["csv"]["rows"] == 2
    assert result["traffic"]["legacy_requests"] == 0
    assert result["traffic"]["django_requests"] == 2
