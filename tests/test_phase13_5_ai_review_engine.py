import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = PROJECT_ROOT / "ai-review"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from evidence_collector import collect_evidence
from ollama_phase_reviewer import production_language_detected, review_phase
from report_generator import generate_report
from requirement_validator import validate_requirements
from test_executor import execute_tests


DOCS = PROJECT_ROOT / "docs"
AI_REVIEW_DOCS = DOCS / "ai-review"


def test_engine_files_exist():
    required = [
        DOCS / "codex-prompts" / "PHASE_13.5_AI_PHASE_REVIEW_ENGINE.md",
        AI_REVIEW_DOCS / "AI_PHASE_REVIEW_ENGINE_ARCHITECTURE.md",
        ENGINE_DIR / "config.yml",
        ENGINE_DIR / "evidence_collector.py",
        ENGINE_DIR / "requirement_validator.py",
        ENGINE_DIR / "test_executor.py",
        ENGINE_DIR / "ollama_phase_reviewer.py",
        ENGINE_DIR / "report_generator.py",
        ENGINE_DIR / "run_phase_review.py",
    ]

    for path in required:
        assert path.exists(), f"Missing AI review engine artifact: {path}"
        assert path.stat().st_size > 0


def test_evidence_collection(tmp_path):
    result = collect_evidence(phase="13.5", output_path=tmp_path / "current_phase.json")

    assert result["phase"] == "13.5"
    assert result["requirement_file"].endswith("PHASE_13.5_AI_PHASE_REVIEW_ENGINE.md")
    assert result["git"]["branch"]
    assert result["safety"]["production_approved"] is False
    assert result["safety"]["code_modified_by_ai"] is False


def test_requirement_validation(tmp_path):
    evidence_path = tmp_path / "current_phase.json"
    collect_evidence(phase="13.5", output_path=evidence_path)

    result = validate_requirements(
        evidence_path=evidence_path,
        output_path=tmp_path / "rule_validation.json",
    )

    assert result["status"] == "PASS"
    assert result["safety"]["production_approval_allowed"] is False
    assert result["safety"]["code_auto_modify_allowed"] is False
    assert result["safety"]["failed_test_bypass_allowed"] is False


def test_test_executor_dry_run(tmp_path):
    result = execute_tests(output_path=tmp_path / "test_result.json", include_migration=False, dry_run=True)

    assert result["status"] == "PASS"
    assert result["safety"]["failed_tests_skipped"] is False
    assert result["safety"]["production_deployed"] is False


def test_ollama_unavailable_handling(tmp_path):
    evidence_path = tmp_path / "current_phase.json"
    rule_path = tmp_path / "rule_validation.json"
    test_path = tmp_path / "test_result.json"

    evidence_path.write_text(json.dumps({"phase": "13.5", "safety": {}}), encoding="utf-8")
    rule_path.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
    test_path.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")

    result = review_phase(
        evidence_path=evidence_path,
        rule_path=rule_path,
        test_path=test_path,
        output_path=tmp_path / "ai_review.json",
        ollama_url="http://127.0.0.1:1",
    )

    assert result["status"] == "WARNING"
    assert result["safety"]["production_approved"] is False
    assert result["safety"]["code_modified_by_ai"] is False
    assert result["safety"]["failed_tests_skipped"] is False


def test_production_approval_language_is_detected():
    assert production_language_detected("The system is ready for production.") is True
    assert production_language_detected("Human review remains required.") is False


def test_report_generation(tmp_path):
    evidence_path = tmp_path / "current_phase.json"
    rule_path = tmp_path / "rule_validation.json"
    test_path = tmp_path / "test_result.json"
    ai_path = tmp_path / "ai_review.json"
    output_path = tmp_path / "PHASE_AI_REVIEW_REPORT.md"

    evidence_path.write_text(json.dumps({"phase": "13.5"}), encoding="utf-8")
    rule_path.write_text(json.dumps({"status": "PASS", "missing": [], "warnings": [], "forbidden_changes": []}), encoding="utf-8")
    test_path.write_text(json.dumps({"status": "PASS", "failed_required": [], "duration_seconds": 0}), encoding="utf-8")
    ai_path.write_text(json.dumps({"status": "WARNING", "summary": "fallback", "issues": [], "recommendation": "review", "ollama": {}}), encoding="utf-8")

    result = generate_report(
        evidence_path=evidence_path,
        rule_path=rule_path,
        test_path=test_path,
        ai_path=ai_path,
        output_path=output_path,
    )

    assert result["decision"] == "WARNING"
    assert result["production_approved"] is False
    assert "Human approval required" in output_path.read_text(encoding="utf-8")
