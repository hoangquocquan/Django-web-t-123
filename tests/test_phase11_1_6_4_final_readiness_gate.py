import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase11_1_6_3_approval_validator import REQUIRED_DOCUMENTS
from scripts.phase11_1_6_4_final_readiness_gate import evaluate_final_readiness


VALID_EVIDENCE = {
    "status": "COMPLETE_EVIDENCE_PACKAGE",
    "ready_for_shutdown": True,
    "environment": "production",
    "simulation": False,
    "source": "iis_w3c_logs_and_csv",
    "collection_period": "2026-07-20 to 2026-07-26",
    "approved_by": "ops-owner",
    "legacy_requests": 0,
    "django_requests": 5,
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


def write_approval_package(directory, overrides=None):
    overrides = overrides or {}
    for config in REQUIRED_DOCUMENTS.values():
        lines = [f"# {config['filename']}", ""]
        for field in config["fields"]:
            value = overrides.get(field, APPROVAL_VALUES.get(field, "approved"))
            lines.append(f"{field}: {value}")
            lines.append("")
        path = Path(directory) / config["filename"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")


def write_rollback_files(tmp_path):
    procedure = tmp_path / "rollback.md"
    checkpoint = tmp_path / "checkpoint.json"
    procedure.write_text("# Rollback\n\nRestore previous /api/* route.", encoding="utf-8")
    write_json(
        checkpoint,
        {
            "rollback_route": "/api/*",
            "replacement_route": "/api/v1/*",
            "restore_action": "restore_previous_router_or_proxy_rule",
        },
    )
    return procedure, checkpoint


def test_missing_evidence_blocked(tmp_path):
    approvals = tmp_path / "approvals"
    write_approval_package(approvals)
    procedure, checkpoint = write_rollback_files(tmp_path)

    result = evaluate_final_readiness(
        evidence_report=tmp_path / "missing-evidence.json",
        approval_dir=approvals,
        rollback_procedure=procedure,
        rollback_checkpoint=checkpoint,
        output_path=tmp_path / "status.json",
    )

    assert result["decision"] == "BLOCKED_SAFELY"
    assert result["evidence"] == "FAIL"


def test_missing_approval_blocked(tmp_path):
    evidence = write_json(tmp_path / "evidence.json", VALID_EVIDENCE)
    procedure, checkpoint = write_rollback_files(tmp_path)

    result = evaluate_final_readiness(
        evidence_report=evidence,
        approval_dir=tmp_path / "missing-approvals",
        rollback_procedure=procedure,
        rollback_checkpoint=checkpoint,
        output_path=tmp_path / "status.json",
    )

    assert result["decision"] == "BLOCKED_SAFELY"
    assert result["approval"] == "FAIL"


def test_missing_rollback_blocked(tmp_path):
    evidence = write_json(tmp_path / "evidence.json", VALID_EVIDENCE)
    approvals = tmp_path / "approvals"
    write_approval_package(approvals)

    result = evaluate_final_readiness(
        evidence_report=evidence,
        approval_dir=approvals,
        rollback_procedure=tmp_path / "missing-rollback.md",
        rollback_checkpoint=tmp_path / "missing-checkpoint.json",
        output_path=tmp_path / "status.json",
    )

    assert result["decision"] == "BLOCKED_SAFELY"
    assert result["rollback"] == "FAIL"


def test_complete_package_accepted(tmp_path):
    evidence = write_json(tmp_path / "evidence.json", VALID_EVIDENCE)
    approvals = tmp_path / "approvals"
    write_approval_package(approvals)
    procedure, checkpoint = write_rollback_files(tmp_path)

    result = evaluate_final_readiness(
        evidence_report=evidence,
        approval_dir=approvals,
        rollback_procedure=procedure,
        rollback_checkpoint=checkpoint,
        output_path=tmp_path / "status.json",
    )

    assert result["decision"] == "READY_TO_EXECUTE_PRODUCTION"
    assert result["evidence"] == "PASS"
    assert result["approval"] == "PASS"
    assert result["rollback"] == "PASS"
    assert result["monitoring"] == "PASS"


def test_unknown_clients_detected(tmp_path):
    evidence_payload = VALID_EVIDENCE.copy()
    evidence_payload["unknown_clients"] = 1
    evidence = write_json(tmp_path / "evidence.json", evidence_payload)
    approvals = tmp_path / "approvals"
    write_approval_package(approvals)
    procedure, checkpoint = write_rollback_files(tmp_path)

    result = evaluate_final_readiness(
        evidence_report=evidence,
        approval_dir=approvals,
        rollback_procedure=procedure,
        rollback_checkpoint=checkpoint,
        output_path=tmp_path / "status.json",
    )

    assert result["decision"] == "BLOCKED_SAFELY"
    assert result["evidence"] == "FAIL"
    assert "Unknown client count is not 0." in result["gates"]["evidence"]["errors"]
