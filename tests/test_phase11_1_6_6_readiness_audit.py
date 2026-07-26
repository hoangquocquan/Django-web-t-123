import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase11_1_6_execute_legacy_api_decommission import execute_legacy_api_decommission
from scripts.phase11_1_6_pre_shutdown_validation import evaluate_pre_shutdown_validation


PRODUCTION_TRAFFIC_REPORT = (
    PROJECT_ROOT
    / "docs"
    / "migration"
    / "production_evidence"
    / "reports"
    / "REAL_PRODUCTION_TRAFFIC_REPORT.json"
)
SIMULATION_EVIDENCE_REPORT = (
    PROJECT_ROOT
    / "docs"
    / "migration"
    / "production_evidence"
    / "reports"
    / "REAL_PRODUCTION_EVIDENCE_REPORT.json"
)
PRODUCTION_STATUS = PROJECT_ROOT / "docs" / "migration" / "phase11_1_6_execution" / "FINAL_READINESS_STATUS.json"
SIMULATION_STATUS = (
    PROJECT_ROOT
    / "docs"
    / "migration"
    / "phase11_1_6_execution"
    / "FINAL_READINESS_SIMULATION_STATUS.json"
)
AUDIT_REPORT = PROJECT_ROOT / "docs" / "reviews" / "PHASE_11.1.6_READINESS_AUDIT_REPORT.md"


APPROVED_ENV = {
    "PHASE11_1_6_TECHNICAL_APPROVAL": "approved",
    "PHASE11_1_6_BUSINESS_APPROVAL": "approved",
    "PHASE11_1_6_ROLLBACK_OWNER": "ops-owner",
    "PHASE11_1_6_MAINTENANCE_WINDOW": "approved",
    "PHASE11_1_6_MONITORING_READY": "approved",
}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_simulation_status_file_cannot_unlock_production():
    """Status mô phỏng không được dùng như evidence production để mở shutdown."""
    simulation_status_payload = load_json(SIMULATION_STATUS)

    result = evaluate_pre_shutdown_validation(evidence=simulation_status_payload, env=APPROVED_ENV)

    assert result["status"] == "BLOCKED_SAFELY"
    assert result["execution_allowed"] is False


def test_default_production_execution_remains_blocked_by_real_inputs(tmp_path):
    """Luồng production mặc định vẫn bị chặn dù có tồn tại report training."""
    result = execute_legacy_api_decommission(env=APPROVED_ENV, output_dir=tmp_path / "execution")

    assert result["status"] == "BLOCKED_SAFELY"
    assert result["execution_status"] == "NOT_EXECUTED"
    assert result["execution_record"]["route_disable_plan"]["script_applies_change"] is False


def test_missing_production_evidence_blocks_shutdown(tmp_path):
    result = evaluate_pre_shutdown_validation(evidence_report_path=tmp_path / "missing.json", env=APPROVED_ENV)

    assert result["status"] == "BLOCKED_SAFELY"
    assert result["execution_allowed"] is False
    assert any("Evidence report does not exist" in error for error in result["errors"])


def test_missing_approval_blocks_shutdown():
    production_evidence = load_json(PRODUCTION_TRAFFIC_REPORT)

    result = evaluate_pre_shutdown_validation(evidence=production_evidence, env={})

    assert result["status"] == "BLOCKED_SAFELY"
    assert result["approval_status"] == "PENDING_OR_INCOMPLETE"


def test_status_separation_works():
    production_status = load_json(PRODUCTION_STATUS)
    simulation_status = load_json(SIMULATION_STATUS)

    assert PRODUCTION_STATUS != SIMULATION_STATUS
    assert production_status["decision"] == "BLOCKED_SAFELY"
    assert simulation_status["decision"] == "READY_TO_EXECUTE_TRAINING"


def test_audit_reports_simulation_evidence_gate_risk():
    """Audit ghi rõ rủi ro: validator production chưa tự reject simulation evidence."""
    simulation_evidence = load_json(SIMULATION_EVIDENCE_REPORT)
    result = evaluate_pre_shutdown_validation(evidence=simulation_evidence, env=APPROVED_ENV)
    audit_text = AUDIT_REPORT.read_text(encoding="utf-8")

    assert simulation_evidence["simulation"] is True
    assert result["status"] == "READY_TO_EXECUTE"
    assert "does not explicitly reject `simulation = true`" in audit_text
    assert "BLOCKED_FOR_PRODUCTION" in audit_text
