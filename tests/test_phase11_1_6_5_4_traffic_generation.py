import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase11_1_6_5_production_evidence_validator import validate_production_evidence_package
from scripts.phase11_1_6_5_4_generate_iis_logs import generate_iis_logs
from scripts.phase11_1_6_5_4_generate_production_like_traffic import generate_traffic


def test_legacy_traffic_remains_zero(tmp_path):
    result = generate_traffic(
        output_path=tmp_path / "traffic.json",
        summary_path=tmp_path / "traffic_generation_summary.json",
        requests=1000,
        days=7,
    )

    assert result["summary"]["legacy_requests"] == 0
    assert all(item["endpoint"].startswith("/api/v1") for item in result["requests"])


def test_django_traffic_generated(tmp_path):
    result = generate_traffic(
        output_path=tmp_path / "traffic.json",
        summary_path=tmp_path / "traffic_generation_summary.json",
        requests=1200,
        clients=6,
        days=7,
    )
    summary = json.loads((tmp_path / "traffic_generation_summary.json").read_text(encoding="utf-8"))

    assert result["summary"]["total_requests"] == 1200
    assert result["summary"]["django_requests"] == 1200
    assert result["clients"] == 6
    assert summary["total_requests"] == 1200
    assert summary["django_requests"] == 1200


def test_iis_log_format_valid(tmp_path):
    traffic_path = tmp_path / "traffic.json"
    generate_traffic(output_path=traffic_path, summary_path=tmp_path / "summary.json", requests=10, days=1)
    output = generate_iis_logs(
        traffic_path=traffic_path,
        log_path=tmp_path / "input" / "iis_logs" / "u_ex_training.log",
        csv_path=tmp_path / "input" / "iis_api_evidence.csv",
        metadata_path=tmp_path / "handover" / "collection_metadata.json",
    )
    log_content = Path(output["iis_log_path"]).read_text(encoding="utf-8")

    assert "#Fields: date time c-ip cs-method cs-uri-stem sc-status cs(User-Agent)" in log_content
    assert "/api/v1/" in log_content


def test_metadata_generated(tmp_path):
    traffic_path = tmp_path / "traffic.json"
    generate_traffic(output_path=traffic_path, summary_path=tmp_path / "summary.json", requests=10, days=1)
    output = generate_iis_logs(
        traffic_path=traffic_path,
        log_path=tmp_path / "input" / "iis_logs" / "u_ex_training.log",
        csv_path=tmp_path / "input" / "iis_api_evidence.csv",
        metadata_path=tmp_path / "handover" / "collection_metadata.json",
    )

    metadata = json.loads(Path(output["metadata_path"]).read_text(encoding="utf-8"))
    assert metadata["server"] == "TRAINING-IIS-SERVER"
    assert metadata["environment"] == "STAGING_SIMULATION"
    assert metadata["operator"] == "training-user"


def test_validator_marks_simulation_evidence_training_only(tmp_path):
    traffic_path = tmp_path / "traffic.json"
    generate_traffic(output_path=traffic_path, summary_path=tmp_path / "summary.json", requests=1000, days=7)
    generate_iis_logs(
        traffic_path=traffic_path,
        log_path=tmp_path / "input" / "iis_logs" / "u_ex_training.log",
        csv_path=tmp_path / "input" / "iis_api_evidence.csv",
        metadata_path=tmp_path / "handover" / "collection_metadata.json",
    )

    with (tmp_path / "input" / "iis_api_evidence.csv").open("r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    result = validate_production_evidence_package(
        input_dir=tmp_path / "input",
        output_path=tmp_path / "report.json",
        review_path=tmp_path / "review.md",
        period="STAGING_SIMULATION 7 days",
    )

    assert len(rows) == 1000
    assert result["status"] == "TRAINING_ONLY"
    assert result["ready_for_shutdown"] is False
    assert result["evidence_type"] == "STAGING_SIMULATION_EVIDENCE"
    assert result["legacy_requests"] == 0
    assert result["django_requests"] >= 1000
    assert result["unknown_clients"] == 0
