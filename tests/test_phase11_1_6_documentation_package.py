import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEWS = PROJECT_ROOT / "docs" / "reviews"
EXECUTION = PROJECT_ROOT / "docs" / "migration" / "phase11_1_6_execution"


REQUIRED_DOCUMENTS = [
    REVIEWS / "PHASE_11.1.6_EXECUTIVE_SUMMARY.md",
    REVIEWS / "PHASE_11.1.6_ARCHITECTURE_HANDOVER.md",
    REVIEWS / "PHASE_11.1.6_OPERATIONS_HANDOVER.md",
    REVIEWS / "PHASE_11.1.6_COMPLIANCE_RECORD.md",
    REVIEWS / "PHASE_11.1.6_STATUS_DASHBOARD.md",
    REVIEWS / "PHASE_11.1.6_FINAL_REVIEW_REPORT.md",
]


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_required_documents_exist():
    for document in REQUIRED_DOCUMENTS:
        assert document.exists(), f"Missing document: {document}"
        assert document.stat().st_size > 0


def test_status_dashboard_exists_and_lists_all_phases():
    dashboard = read_text(REVIEWS / "PHASE_11.1.6_STATUS_DASHBOARD.md")

    for phase in ["11.1.6.1", "11.1.6.2", "11.1.6.3", "11.1.6.4", "11.1.6.5", "11.1.6.6", "11.1.6.7"]:
        assert phase in dashboard
    assert "READY_TO_EXECUTE_TRAINING" in dashboard
    assert "BLOCKED_SAFELY" in dashboard


def test_production_training_separation_documented():
    combined = "\n".join(read_text(document) for document in REQUIRED_DOCUMENTS)

    assert "READY_TO_EXECUTE_TRAINING" in combined
    assert "READY_TO_EXECUTE_PRODUCTION" in combined
    assert "BLOCKED_SAFELY" in combined
    assert "simulation cannot unlock production" in combined.lower()


def test_no_shutdown_executed_in_status_files():
    production_status = load_json(EXECUTION / "FINAL_READINESS_STATUS.json")
    simulation_status = load_json(EXECUTION / "FINAL_READINESS_SIMULATION_STATUS.json")

    assert production_status["decision"] == "BLOCKED_SAFELY"
    assert simulation_status["decision"] == "READY_TO_EXECUTE_TRAINING"
    assert production_status["safety"]["shutdown_executed"] is False
    assert simulation_status["safety"]["shutdown_executed"] is False
    assert production_status["safety"]["legacy_api_disabled"] is False
    assert simulation_status["safety"]["legacy_api_disabled"] is False
