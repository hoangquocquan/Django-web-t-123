import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.n8n_ollama_review import generate_review
from scripts.n8n_phase_trigger import create_execution_report
from scripts.phase_validator import validate_phase


DOCS = PROJECT_ROOT / "docs"
N8N = DOCS / "n8n"
AI_DEVOPS = DOCS / "ai-devops"
REVIEWS = DOCS / "reviews"


def read(path):
    return Path(path).read_text(encoding="utf-8")


def test_n8n_artifacts_exist():
    required = [
        DOCS / "codex-prompts" / "PHASE_13.3_N8N_CICD_ORCHESTRATION.md",
        N8N / "N8N_CICD_ARCHITECTURE.md",
        N8N / "n8n_cicd_pipeline_workflow.json",
        N8N / "N8N_SETUP_GUIDE.md",
        N8N / "N8N_NOTIFICATION_DESIGN.md",
        PROJECT_ROOT / "scripts" / "n8n_phase_trigger.py",
        PROJECT_ROOT / "scripts" / "n8n_ollama_review.py",
        REVIEWS / "PHASE_13.3_N8N_CICD_REPORT.md",
    ]

    for path in required:
        assert path.exists(), f"Missing n8n artifact: {path}"
        assert path.stat().st_size > 0


def test_workflow_has_required_nodes_and_no_production_deploy():
    workflow = json.loads((N8N / "n8n_cicd_pipeline_workflow.json").read_text(encoding="utf-8"))
    node_names = {node["name"] for node in workflow["nodes"]}
    serialized = json.dumps(workflow).lower()

    assert {
        "Git trigger",
        "Receive event",
        "Validate phase",
        "Run tests",
        "Build Docker image",
        "Call Ollama API",
        "Generate report",
        "Notification",
    }.issubset(node_names)
    assert workflow["active"] is False
    assert workflow["meta"]["productionDeploymentIncluded"] is False
    assert workflow["meta"]["realSecretsIncluded"] is False
    assert "deploy production" not in serialized
    assert "production deployment" not in serialized


def test_security_rules_are_documented():
    architecture = read(N8N / "N8N_CICD_ARCHITECTURE.md")
    notifications = read(N8N / "N8N_NOTIFICATION_DESIGN.md")
    setup = read(N8N / "N8N_SETUP_GUIDE.md")

    assert "Do not deploy production automatically" in architecture
    assert "Do not approve production automatically" in architecture
    assert "n8n cannot approve production" in notifications
    assert "Do not commit real values" in setup


def test_phase_trigger_generates_local_dry_run_report(tmp_path):
    report = create_execution_report(output_path=tmp_path / "n8n_execution_report.json", local_only=True)

    assert report["mode"] == "local_dry_run"
    assert report["status"] == "N8N_ORCHESTRATION_COMPLETE"
    assert report["safety"]["production_deployed"] is False
    assert report["safety"]["real_secrets_stored"] is False
    assert report["safety"]["human_approval_bypassed"] is False
    assert report["safety"]["ci_testing_replaced"] is False


def test_n8n_ai_review_is_advisory(tmp_path):
    execution_path = tmp_path / "n8n_execution_report.json"
    pipeline_path = tmp_path / "test_pipeline_result.json"
    output_path = tmp_path / "N8N_AI_REVIEW_REPORT.md"

    execution_path.write_text(
        json.dumps(
            {
                "status": "N8N_ORCHESTRATION_COMPLETE",
                "mode": "local_dry_run",
                "webhook_configured": False,
                "safety": {
                    "production_deployed": False,
                    "real_secrets_stored": False,
                    "human_approval_bypassed": False,
                    "ci_testing_replaced": False,
                },
            }
        ),
        encoding="utf-8",
    )
    pipeline_path.write_text(
        json.dumps(
            {
                "summary": {
                    "status": "TEST_PIPELINE_COMPLETE",
                    "passed_tests": 1,
                    "failed_tests": 0,
                    "warnings": 0,
                }
            }
        ),
        encoding="utf-8",
    )

    review = generate_review(
        execution_path=execution_path,
        pipeline_path=pipeline_path,
        output_path=output_path,
        ollama_url="http://127.0.0.1:1",
    )

    assert review["decision"] == "PASS_WITH_WARNING"
    assert review["auto_deploy"] is False
    assert review["auto_approve_production"] is False
    assert output_path.exists()
    assert "advisory only" in output_path.read_text(encoding="utf-8")


def test_phase_validator_knows_phase13_3(tmp_path):
    result = validate_phase(phase="13.3", output_path=tmp_path / "phase_validation_result.json")

    assert result["phase"] == "13.3"
    assert result["safety"]["auto_deploy"] is False
    assert result["safety"]["auto_approve_production"] is False
