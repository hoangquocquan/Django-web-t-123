import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEWS = PROJECT_ROOT / "docs" / "reviews"
EXECUTION = PROJECT_ROOT / "docs" / "migration" / "phase11_1_6_execution"


MASTER_DOCUMENTS = [
    REVIEWS / "PHASE_11_MASTER_EXECUTIVE_SUMMARY.md",
    REVIEWS / "PHASE_11_TECHNICAL_MASTER_REPORT.md",
    REVIEWS / "PHASE_11_OPERATIONS_MASTER_RUNBOOK.md",
    REVIEWS / "PHASE_11_RISK_REGISTER.md",
    REVIEWS / "PHASE_11_TIMELINE.md",
    REVIEWS / "PHASE_11_MASTER_STATUS_DASHBOARD.md",
    REVIEWS / "PHASE_11_FINAL_REVIEW_REPORT.md",
]


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_all_master_documents_exist():
    for document in MASTER_DOCUMENTS:
        assert document.exists(), f"Missing master document: {document}"
        assert document.stat().st_size > 0


def test_no_production_shutdown_executed():
    production_status = load_json(EXECUTION / "FINAL_READINESS_STATUS.json")
    simulation_status = load_json(EXECUTION / "FINAL_READINESS_SIMULATION_STATUS.json")

    assert production_status["decision"] == "BLOCKED_SAFELY"
    assert production_status["safety"]["shutdown_executed"] is False
    assert production_status["safety"]["legacy_api_disabled"] is False
    assert simulation_status["decision"] == "READY_TO_EXECUTE_TRAINING"
    assert simulation_status["safety"]["shutdown_executed"] is False


def test_production_blocked_status_documented():
    combined = "\n".join(read_text(document) for document in MASTER_DOCUMENTS)

    assert "BLOCKED_SAFELY" in combined
    assert "READY_TO_EXECUTE_TRAINING" in combined
    assert "READY_TO_EXECUTE_PRODUCTION" in combined
    assert "Do not execute shutdown" in combined


def test_master_dashboard_covers_phase_11_scope():
    dashboard = read_text(REVIEWS / "PHASE_11_MASTER_STATUS_DASHBOARD.md")

    for phase in ["11.0", "11.1", "11.1.1", "11.1.2", "11.1.3", "11.1.4", "11.1.5", "11.1.6"]:
        assert phase in dashboard
