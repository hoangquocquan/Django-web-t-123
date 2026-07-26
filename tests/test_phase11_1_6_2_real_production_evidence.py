import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase11_1_6_2_real_production_evidence import validate_real_production_evidence


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["timestamp", "client", "endpoint", "status_code", "user_agent"])
        writer.writeheader()
        writer.writerows(rows)


def test_empty_evidence_blocked(tmp_path):
    report_path = tmp_path / "report.json"

    result = validate_real_production_evidence(input_dir=tmp_path, output_path=report_path)

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert "No production evidence files were found." in result["errors"]
    assert report_path.exists()


def test_legacy_traffic_detected(tmp_path):
    write_csv(
        tmp_path / "api.csv",
        [
            {
                "timestamp": "2026-07-26T01:00:00Z",
                "client": "client-a",
                "endpoint": "/api/products",
                "status_code": "200",
                "user_agent": "integration-test",
            },
            {
                "timestamp": "2026-07-26T01:01:00Z",
                "client": "client-a",
                "endpoint": "/api/v1/catalog/products/",
                "status_code": "200",
                "user_agent": "integration-test",
            },
        ],
    )

    result = validate_real_production_evidence(input_dir=tmp_path, output_path=tmp_path / "report.json")

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert result["legacy_requests"] == 1
    assert "Legacy `/api/*` traffic was detected." in result["errors"]


def test_zero_legacy_traffic_and_django_traffic_confirmed(tmp_path):
    write_csv(
        tmp_path / "api.csv",
        [
            {
                "timestamp": "2026-07-26T01:00:00Z",
                "client": "client-a",
                "endpoint": "/api/v1/catalog/products/",
                "status_code": "200",
                "user_agent": "integration-test",
            },
            {
                "timestamp": "2026-07-26T01:01:00Z",
                "client": "client-b",
                "endpoint": "/api/v1/crm/contact-requests/",
                "status_code": "200",
                "user_agent": "integration-test",
            },
        ],
    )

    result = validate_real_production_evidence(input_dir=tmp_path, output_path=tmp_path / "report.json")

    assert result["status"] == "COMPLETE_EVIDENCE_PACKAGE"
    assert result["legacy_requests"] == 0
    assert result["django_requests"] == 2
    assert result["unknown_clients"] == 0
    assert result["ready_for_shutdown"] is True


def test_json_gateway_log_supported(tmp_path):
    gateway_log = tmp_path / "gateway.jsonl"
    gateway_log.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "timestamp": "2026-07-26T01:00:00Z",
                        "client": "client-a",
                        "path": "/api/v1/sales/quotes/",
                        "status": 200,
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-07-26T01:01:00Z",
                        "client": "client-b",
                        "path": "/api/v1/news/",
                        "status": 200,
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    result = validate_real_production_evidence(input_dir=tmp_path, output_path=tmp_path / "report.json")

    assert result["status"] == "COMPLETE_EVIDENCE_PACKAGE"
    assert result["django_requests"] == 2


def test_unknown_client_detected(tmp_path):
    write_csv(
        tmp_path / "api.csv",
        [
            {
                "timestamp": "2026-07-26T01:00:00Z",
                "client": "",
                "endpoint": "/api/v1/catalog/products/",
                "status_code": "200",
                "user_agent": "integration-test",
            },
        ],
    )

    result = validate_real_production_evidence(input_dir=tmp_path, output_path=tmp_path / "report.json")

    assert result["status"] == "INCOMPLETE_EVIDENCE_PACKAGE"
    assert result["unknown_clients"] == 1
    assert "Unknown API clients were detected." in result["errors"]
