import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase11_1_6_3_approval_validator import REQUIRED_DOCUMENTS
from scripts.phase11_1_6_4_1_readiness_simulation import build_training_readiness


VALID_SIMULATION_EVIDENCE = {
    "status": "COMPLETE_EVIDENCE_PACKAGE",
    "ready_for_shutdown": True,
    "environment": "STAGING_SIMULATION",
    "simulation": True,
    "legacy_requests": 0,
    "django_requests": 12,
    "unknown_clients": 0,
    "routes_changed": False,
    "proxy_modified": False,
    "shutdown_executed": False,
}


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def write_pending_approval_templates(directory):
    """Tạo approval PENDING để mô phỏng đúng trạng thái chưa ký thật."""
    directory.mkdir(parents=True, exist_ok=True)
    for config in REQUIRED_DOCUMENTS.values():
        lines = [f"# {config['filename']}", ""]
        for field in config["fields"]:
            lines.append(f"{field}: PENDING")
            lines.append("")
        if config["filename"] == "MONITORING_OWNER.md":
            lines.extend(
                [
                    "## Monitoring Scope",
                    "",
                    "- `/api/*` attempts will be watched after shutdown.",
                    "- `/api/v1/*` traffic will be watched during and after the maintenance window.",
                    "- Error rate and latency will be monitored.",
                    "- Escalation path is known before shutdown.",
                ]
            )
        (directory / config["filename"]).write_text("\n".join(lines), encoding="utf-8")


def write_rollback_files(tmp_path):
    procedure = tmp_path / "LEGACY_API_DECOMMISSION_ROLLBACK.md"
    procedure.write_text(
        "# Legacy API Decommission Rollback\n\n## Rollback Steps\n\n1. Restore previous `/api/*` route.",
        encoding="utf-8",
    )
    checkpoint = write_json(
        tmp_path / "rollback-checkpoint.json",
        {
            "rollback_route": "/api/*",
            "replacement_route": "/api/v1/*",
            "restore_action": "restore_previous_router_or_proxy_rule",
        },
    )
    return procedure, checkpoint


def write_runbook(tmp_path):
    runbook = tmp_path / "runbook.md"
    runbook.write_text(
        "\n".join(
            [
                "# Runbook",
                "",
                "Track legacy `/api/*` attempts.",
                "Track replacement `/api/v1/*` traffic.",
                "Track error rate, latency and unknown clients.",
            ]
        ),
        encoding="utf-8",
    )
    return runbook


def build_result(tmp_path, evidence_payload=None):
    evidence = write_json(tmp_path / "evidence.json", evidence_payload or VALID_SIMULATION_EVIDENCE)
    approvals = tmp_path / "approvals"
    write_pending_approval_templates(approvals)
    rollback_procedure, rollback_checkpoint = write_rollback_files(tmp_path)
    runbook = write_runbook(tmp_path)

    return build_training_readiness(
        evidence_report=evidence,
        approval_dir=approvals,
        rollback_procedure=rollback_procedure,
        rollback_checkpoint=rollback_checkpoint,
        status_output=tmp_path / "status.json",
        review_output=tmp_path / "review.md",
        runbook_path=runbook,
    )


def test_simulation_evidence_accepted(tmp_path):
    result = build_result(tmp_path)

    assert result["decision"] == "READY_TO_EXECUTE_TRAINING"
    assert result["evidence"] == "PASS"
    assert result["approval_simulation"] == "TRAINING_APPROVAL_SIMULATION"


def test_legacy_traffic_zero(tmp_path):
    result = build_result(tmp_path)

    assert result["gates"]["evidence"]["legacy_requests"] == 0


def test_django_traffic_exists(tmp_path):
    result = build_result(tmp_path)

    assert result["gates"]["evidence"]["django_requests"] > 0


def test_readiness_report_generated(tmp_path):
    result = build_result(tmp_path)
    report_path = Path(result["review_report"])

    assert report_path.exists()
    assert "READY_TO_EXECUTE_TRAINING" in report_path.read_text(encoding="utf-8")


def test_non_simulation_evidence_blocked(tmp_path):
    evidence = VALID_SIMULATION_EVIDENCE.copy()
    evidence["simulation"] = False

    result = build_result(tmp_path, evidence_payload=evidence)

    assert result["decision"] == "BLOCKED_SAFELY"
    assert result["evidence"] == "FAIL"
