import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase13_2_test_ai_review import generate_ai_review
from scripts.phase13_2_test_pipeline import run_pipeline
from scripts.phase_validator import validate_phase


DOCS = PROJECT_ROOT / "docs"
CICD = DOCS / "cicd"
AI_DEVOPS = DOCS / "ai-devops"
REVIEWS = DOCS / "reviews"


def read(path):
    return Path(path).read_text(encoding="utf-8")


def test_pipeline_files_exist():
    required = [
        DOCS / "codex-prompts" / "PHASE_13.2_AUTOMATED_TEST_PIPELINE.md",
        CICD / "TEST_PIPELINE_ARCHITECTURE.md",
        PROJECT_ROOT / "ci" / "test_pipeline_config.yml",
        PROJECT_ROOT / ".github" / "workflows" / "test_pipeline.yml",
        PROJECT_ROOT / "scripts" / "phase13_2_test_pipeline.py",
        PROJECT_ROOT / "scripts" / "phase13_2_test_ai_review.py",
        REVIEWS / "PHASE_13.2_TEST_PIPELINE_REPORT.md",
    ]

    for path in required:
        assert path.exists(), f"Missing Phase 13.2 artifact: {path}"
        assert path.stat().st_size > 0


def test_runner_generates_evidence_without_deploying(tmp_path):
    result = run_pipeline(output_path=tmp_path / "test_pipeline_result.json", dry_run=True)

    assert result["summary"]["status"] == "TEST_PIPELINE_COMPLETE"
    assert result["safety"]["production_deployed"] is False
    assert result["safety"]["real_ci_secrets_created"] is False
    assert result["safety"]["failed_tests_bypassed"] is False
    assert {stage["name"] for stage in result["stages"]} >= {
        "dependency_check",
        "lint_check",
        "unit_tests",
        "integration_tests",
        "security_tests",
        "migration_tests",
    }


def test_config_and_workflow_do_not_deploy_production():
    config = read(PROJECT_ROOT / "ci" / "test_pipeline_config.yml")
    workflow = read(PROJECT_ROOT / ".github" / "workflows" / "test_pipeline.yml")

    assert "deploy_production: false" in config
    assert "create_real_ci_secrets: false" in config
    assert "pull_request" in workflow
    assert "push" in workflow
    assert "deploy production" not in workflow.lower()
    assert "production deployment" not in workflow.lower()


def test_ai_review_generates_advisory_report(tmp_path):
    result_path = tmp_path / "test_pipeline_result.json"
    output_path = tmp_path / "TEST_PIPELINE_AI_REVIEW.md"
    result_path.write_text(
        json.dumps(
            {
                "summary": {
                    "status": "TEST_PIPELINE_COMPLETE",
                    "passed_tests": 3,
                    "failed_tests": 0,
                    "warnings": 1,
                    "failed_required_stages": [],
                },
                "stages": [],
                "safety": {
                    "production_deployed": False,
                    "real_ci_secrets_created": False,
                    "failed_tests_bypassed": False,
                },
            }
        ),
        encoding="utf-8",
    )

    review = generate_ai_review(result_path=result_path, output_path=output_path, ollama_url="http://127.0.0.1:1")

    assert review["decision"] == "PASS_WITH_WARNING"
    assert review["auto_deploy"] is False
    assert review["auto_approve_production"] is False
    assert output_path.exists()
    assert "advisory only" in output_path.read_text(encoding="utf-8")


def test_phase_validator_knows_phase13_2(tmp_path):
    result = validate_phase(phase="13.2", output_path=tmp_path / "phase_validation_result.json")

    assert result["phase"] == "13.2"
    assert result["safety"]["auto_deploy"] is False
    assert result["safety"]["auto_approve_production"] is False
