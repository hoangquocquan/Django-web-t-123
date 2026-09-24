import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import n8n_phase_trigger


DOCS = PROJECT_ROOT / "docs"
N8N_DOCS = DOCS / "n8n"
N8N = PROJECT_ROOT / "n8n"


def read(path):
    return Path(path).read_text(encoding="utf-8")


def test_controller_artifacts_exist():
    required = [
        DOCS / "codex-prompts" / "PHASE_13.7_N8N_REAL_AUTOMATION_CONTROLLER.md",
        N8N_DOCS / "N8N_REAL_AUTOMATION_ARCHITECTURE.md",
        N8N / "workflows" / "phase_automation_controller.json",
        N8N / "config" / "n8n_phase_controller.yml",
        PROJECT_ROOT / "scripts" / "n8n_phase_trigger.py",
        N8N_DOCS / "N8N_NOTIFICATION_DESIGN.md",
        DOCS / "reviews" / "PHASE_13.7_N8N_AUTOMATION_REPORT.md",
    ]

    for path in required:
        assert path.exists(), f"Missing Phase 13.7 artifact: {path}"
        assert path.stat().st_size > 0


def test_workflow_exists_and_has_required_nodes():
    workflow = json.loads((N8N / "workflows" / "phase_automation_controller.json").read_text(encoding="utf-8"))
    node_names = {node["name"] for node in workflow["nodes"]}

    assert {
        "Webhook Trigger",
        "Phase Input Validator",
        "Run Test Executor",
        "Decision Node",
        "Error Collector",
        "Self Correction Trigger",
        "Ollama Reviewer",
        "Report Generator",
        "Notification",
    }.issubset(node_names)
    assert workflow["active"] is False
    assert workflow["meta"]["productionDeploymentIncluded"] is False
    assert workflow["meta"]["autoMergeIncluded"] is False
    assert workflow["meta"]["humanApprovalRequired"] is True


def test_configuration_has_allowed_commands_and_restrictions():
    config = read(N8N / "config" / "n8n_phase_controller.yml")

    assert "ai-review/run_phase_review.py" in config
    assert "ai-review/retry_controller.py" in config
    assert "auto_deploy_production: false" in config
    assert "auto_merge_code: false" in config
    assert "bypass_human_approval: false" in config
    assert "hide_failed_tests: false" in config


def test_trigger_works_without_real_n8n(monkeypatch, tmp_path):
    def fake_controller(phase="13.7"):
        return {
            "status": "WAITING_HUMAN_APPROVAL",
            "phase_validation": {"status": "PASS"},
            "ai_review": {"status": "PASS"},
            "self_correction": {"status": "PASS"},
        }

    monkeypatch.setattr(n8n_phase_trigger, "run_local_controller", fake_controller)
    result = n8n_phase_trigger.create_automation_history(output_path=tmp_path / "execution_history.json", local_only=True)

    assert result["status"] == "WAITING_HUMAN_APPROVAL"
    assert result["mode"] == "local_controller"
    assert result["safety"]["production_deployed"] is False
    assert result["safety"]["code_auto_merged"] is False
    assert result["safety"]["human_approval_bypassed"] is False
    assert result["safety"]["failed_tests_hidden"] is False


def test_safety_rules_exist_and_no_production_automation():
    architecture = read(N8N_DOCS / "N8N_REAL_AUTOMATION_ARCHITECTURE.md")
    notifications = read(N8N_DOCS / "N8N_NOTIFICATION_DESIGN.md")
    workflow_text = read(N8N / "workflows" / "phase_automation_controller.json").lower()

    assert "auto deploy production" in architecture
    assert "auto merge code" in architecture
    assert "Human approval remains required" in architecture
    assert "n8n cannot auto merge code" in notifications
    assert "deploy production" not in workflow_text
    assert "auto merge" not in workflow_text
