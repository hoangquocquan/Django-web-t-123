import csv
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase11_1_6_3_approval_validator import REQUIRED_DOCUMENTS
from scripts.phase11_1_6_4_final_readiness_gate import evaluate_final_readiness
from scripts.phase11_1_6_5_production_evidence_validator import (
    REQUIRED_CSV_FIELDS,
    validate_production_evidence_package,
)


SIMULATION_EVIDENCE = {
    "status": "TRAINING_ONLY",
    "ready_for_shutdown": False,
    "evidence_type": "STAGING_SIMULATION_EVIDENCE",
    "environment": "STAGING_SIMULATION",
    "simulation": True,
    "source": "iis_w3c_logs_and_csv",
    "collection_period": "2026-07-20 to 2026-07-26",
    "approved_by": "architect-review",
    "legacy_requests": 0,
    "django_requests": 15,
    "unknown_clients": 0,
    "routes_changed": False,
    "proxy_modified": False,
    "shutdown_executed": False,
}


PRODUCTION_EVIDENCE = {
    "status": "COMPLETE_EVIDENCE_PACKAGE",
    "ready_for_shutdown": True,
    "evidence_type": "REAL_PRODUCTION_EVIDENCE",
    "environment": "production",
    "simulation": False,
    "source": "iis_w3c_logs_and_csv",
    "collection_period": "2026-07-20 to 2026-07-26",
    "approved_by": "ops-owner",
    "legacy_requests": 0,
    "django_requests": 15,
    "unknown_clients": 0,
    "routes_changed": False,
    "proxy_modified": False,
    "shutdown_executed": False,
}


APPROVAL_VALUES = {
    "System owner": "Platform Owner",
    "Technical reviewer": "Senior Architect",
    "Evidence confirmation": "approved",
    "Risk assessment": "approved",
    "Rollback validation": "approved",
    "Business owner": "Business Owner",
    "Business impact review": "approved",
    "Customer impact assessment": "approved",
    "Downtime acceptance": "approved",
    "Rollback owner": "Ops Owner",
    "Backup owner": "Backup Ops",
    "Rollback procedure reference": "rollback.md",
    "Contact information": "ops@example.com",
    "Planned execution date": "2026-07-26",
    "Start time": "22:00",
    "End time": "23:00",
    "Timezone": "Asia/Tokyo",
    "Expected impact": "Low",
    "Communication plan": "Support notified",
    "Rollback decision time": "22:30",
    "Monitoring owner": "Monitoring Owner",
    "Monitoring tools": "APM and IIS logs",
    "API errors metric": "5xx rate",
    "Latency metric": "p95 latency",
    "Traffic metric": "request count",
    "HTTP status codes metric": "status distribution",
    "Escalation path": "Ops to Architect",
    "Approval status": "approved",
    "Signature": "Signed",
    "Date": "2026-07-26",
}


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def write_approval_package(directory):
    for config in REQUIRED_DOCUMENTS.values():
        lines = [f"# {config['filename']}", ""]
        for field in config["fields"]:
            lines.append(f"{field}: {APPROVAL_VALUES.get(field, 'approved')}")
            lines.append("")
        path = Path(directory) / config["filename"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")


def write_rollback_files(tmp_path):
    procedure = tmp_path / "rollback.md"
    checkpoint = tmp_path / "checkpoint.json"
    procedure.write_text("# Rollback\n\n## Rollback Steps\n\nRestore previous /api/* route.", encoding="utf-8")
    write_json(
        checkpoint,
        {
            "rollback_route": "/api/*",
            "replacement_route": "/api/v1/*",
            "restore_action": "restore_previous_router_or_proxy_rule",
        },
    )
    return procedure, checkpoint


def evaluate_with_payload(tmp_path, payload, readiness_mode="production"):
    evidence = write_json(tmp_path / "evidence.json", payload)
    approvals = tmp_path / "approvals"
    write_approval_package(approvals)
    procedure, checkpoint = write_rollback_files(tmp_path)
    return evaluate_final_readiness(
        evidence_report=evidence,
        approval_dir=approvals,
        rollback_procedure=procedure,
        rollback_checkpoint=checkpoint,
        output_path=tmp_path / "status.json",
        readiness_mode=readiness_mode,
    )


def write_csv(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=REQUIRED_CSV_FIELDS)
        writer.writeheader()
        writer.writerow(
            {
                "timestamp": "2026-07-20T01:00:00Z",
                "source": "iis",
                "client": "client-a",
                "endpoint": "/api/v1/catalog/products/",
                "status_code": "200",
                "user_agent": "DjangoClient",
            }
        )


def write_iis_log(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "#Software: Microsoft Internet Information Services 10.0",
                "#Fields: date time c-ip cs-method cs-uri-stem sc-status cs(User-Agent)",
                "2026-07-20 01:00:00 10.0.0.10 GET /api/v1/catalog/products/ 200 DjangoClient",
            ]
        ),
        encoding="utf-8",
    )


def write_metadata(input_dir, environment="production", simulation=False):
    metadata_path = Path(input_dir).parent / "handover" / "collection_metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(
            {
                "environment": environment,
                "simulation": simulation,
                "source": "iis_w3c_logs_and_csv",
                "collection_period": "2026-07-20 to 2026-07-26",
                "approved_by": "ops-owner",
                "server": "IIS-PROD-01",
                "iis_site": "MECPrecision-Web",
                "site_id": "1",
            }
        ),
        encoding="utf-8",
    )


def test_simulation_evidence_rejected_for_production(tmp_path):
    result = evaluate_with_payload(tmp_path, SIMULATION_EVIDENCE, readiness_mode="production")

    assert result["decision"] == "BLOCKED_SAFELY"
    assert result["evidence"] == "FAIL"
    assert "Simulation evidence cannot unlock production readiness." in result["gates"]["evidence"]["errors"]


def test_simulation_returns_training_status(tmp_path):
    result = evaluate_with_payload(tmp_path, SIMULATION_EVIDENCE, readiness_mode="training")

    assert result["decision"] == "READY_TO_EXECUTE_TRAINING"
    assert result["gates"]["evidence"]["evidence_type"] == "STAGING_SIMULATION_EVIDENCE"


def test_production_evidence_accepted(tmp_path):
    result = evaluate_with_payload(tmp_path, PRODUCTION_EVIDENCE, readiness_mode="production")

    assert result["decision"] == "READY_TO_EXECUTE_PRODUCTION"
    assert result["gates"]["evidence"]["evidence_type"] == "REAL_PRODUCTION_EVIDENCE"


def test_metadata_required_for_production_evidence(tmp_path):
    evidence = PRODUCTION_EVIDENCE.copy()
    evidence.pop("approved_by")

    result = evaluate_with_payload(tmp_path, evidence, readiness_mode="production")

    assert result["decision"] == "BLOCKED_SAFELY"
    assert "Production evidence metadata `approved_by` is missing." in result["gates"]["evidence"]["errors"]


def test_missing_environment_blocked(tmp_path):
    evidence = PRODUCTION_EVIDENCE.copy()
    evidence.pop("environment")

    result = evaluate_with_payload(tmp_path, evidence, readiness_mode="production")

    assert result["decision"] == "BLOCKED_SAFELY"
    assert "Evidence is not classified as REAL_PRODUCTION_EVIDENCE." in result["gates"]["evidence"]["errors"]


def test_production_validator_marks_simulation_training_only(tmp_path):
    input_dir = tmp_path / "input"
    write_metadata(input_dir, environment="STAGING_SIMULATION", simulation=True)
    write_csv(input_dir / "iis_api_evidence.csv")
    write_iis_log(input_dir / "iis_logs" / "u_ex260720.log")

    result = validate_production_evidence_package(
        input_dir=input_dir,
        output_path=tmp_path / "report.json",
        review_path=tmp_path / "review.md",
        period="2026-07-20 to 2026-07-26",
    )

    assert result["status"] == "TRAINING_ONLY"
    assert result["ready_for_shutdown"] is False
    assert result["decision"] == "TRAINING_ONLY"


def test_production_validator_accepts_real_production_metadata(tmp_path):
    input_dir = tmp_path / "input"
    write_metadata(input_dir, environment="production", simulation=False)
    write_csv(input_dir / "iis_api_evidence.csv")
    write_iis_log(input_dir / "iis_logs" / "u_ex260720.log")

    result = validate_production_evidence_package(
        input_dir=input_dir,
        output_path=tmp_path / "report.json",
        review_path=tmp_path / "review.md",
        period="2026-07-20 to 2026-07-26",
    )

    assert result["status"] == "COMPLETE_EVIDENCE_PACKAGE"
    assert result["ready_for_shutdown"] is True
    assert result["evidence_type"] == "REAL_PRODUCTION_EVIDENCE"
