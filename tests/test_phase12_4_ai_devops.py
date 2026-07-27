import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ollama_phase_reviewer import decide, generate_review
from scripts.phase_validator import validate_phase


AI_DEVOPS_DIR = PROJECT_ROOT / "docs" / "ai-devops"


def test_validator_works(tmp_path):
    result = validate_phase(phase="12.4", output_path=tmp_path / "validation.json")

    assert result["phase"] == "12.4"
    assert result["status"] == "PASS"
    assert result["missing"] == []
    assert result["safety"]["auto_deploy"] is False
    assert result["safety"]["auto_approve_production"] is False
    assert result["safety"]["human_review_required"] is True


def test_ollama_connection_handling(monkeypatch, tmp_path):
    def fake_ollama(prompt, **kwargs):
        return {"available": False, "response": "", "error": "connection refused"}

    monkeypatch.setattr("scripts.ollama_phase_reviewer.ask_ollama", fake_ollama)
    validation_path = tmp_path / "validation.json"
    validation_path.write_text(json.dumps({"status": "PASS", "missing": [], "warnings": []}), encoding="utf-8")

    result = generate_review(validation_path=validation_path, output_path=tmp_path / "review.md")

    assert result["decision"] == "PASS_WITH_WARNING"
    assert result["ollama_available"] is False
    assert result["auto_deploy"] is False
    assert result["auto_approve_production"] is False


def test_report_generation(monkeypatch, tmp_path):
    def fake_ollama(prompt, **kwargs):
        return {"available": True, "model_available": True, "models": ["llama3.1"], "response": "decision: PASS\nhuman review required", "error": ""}

    monkeypatch.setattr("scripts.ollama_phase_reviewer.ask_ollama", fake_ollama)
    validation_path = tmp_path / "validation.json"
    validation_path.write_text(json.dumps({"status": "PASS", "missing": [], "warnings": []}), encoding="utf-8")
    output_path = tmp_path / "AI_PHASE_REVIEW_REPORT.md"

    result = generate_review(validation_path=validation_path, output_path=output_path)

    assert result["decision"] == "PASS"
    assert output_path.exists()
    assert "Human review required" in output_path.read_text(encoding="utf-8")


def test_safety_rules_exist():
    content = (AI_DEVOPS_DIR / "AI_REVIEW_RULES.md").read_text(encoding="utf-8")

    assert "Documentation Completeness" in content
    assert "Production Safety" in content
    assert "approve production deployment" in content


def test_no_automatic_production_approval():
    validation = {"status": "PASS", "warnings": []}
    ollama_result = {"available": True, "response": "decision: PASS"}

    assert decide(validation, ollama_result) == "PASS"
    workflow = json.loads((AI_DEVOPS_DIR / "n8n_phase_review_workflow.json").read_text(encoding="utf-8"))
    safety = workflow["staticData"]["safety"]
    assert safety["autoDeploy"] is False
    assert safety["autoApproveProduction"] is False
    assert safety["humanReviewRequired"] is True
