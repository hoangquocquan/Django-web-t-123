import importlib.util
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FACTORY_DIR = PROJECT_ROOT / "ai-factory"
DOCS = PROJECT_ROOT / "docs"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_template_loading():
    templates = [
        FACTORY_DIR / "templates" / "phase_requirement_template.md",
        FACTORY_DIR / "templates" / "phase_test_template.md",
        FACTORY_DIR / "templates" / "phase_review_template.md",
    ]

    for template in templates:
        assert template.exists()
        content = template.read_text(encoding="utf-8")
        assert "Human" in content or "human" in content
        assert "production" in content.lower()


def test_evidence_generation(tmp_path):
    evidence_builder = load_module("factory_evidence_builder", FACTORY_DIR / "evidence_builder.py")
    output = tmp_path / "package.json"
    package = evidence_builder.build_evidence_package(
        phase="13.8",
        command_results=[
            {
                "command": "pytest tests/test_phase13_8_ai_factory.py",
                "status": "PASS",
                "stdout_tail": "5 passed",
                "stderr_tail": "",
            }
        ],
        correction_result={"status": "NOT_REQUIRED", "reason": "Tests passed."},
        output_path=output,
    )

    assert output.exists()
    assert package["phase"] == "13.8"
    assert package["safety"]["production_deployed"] is False
    assert package["safety"]["code_auto_merged"] is False
    assert package["safety"]["human_approval_required"] is True


def test_report_generation(tmp_path):
    report_generator = load_module("factory_report_generator", FACTORY_DIR / "final_report_generator.py")
    evidence = {
        "phase": "13.8",
        "tests": [{"command": "pytest", "status": "PASS"}],
        "ai_review": {"status": "PASS", "decision": "PASS"},
        "factory_correction": {"status": "NOT_REQUIRED", "reason": "Tests passed."},
    }
    evidence_path = tmp_path / "package.json"
    output_path = tmp_path / "report.md"
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

    result = report_generator.generate_final_report(evidence_path=evidence_path, output_path=output_path)
    report = output_path.read_text(encoding="utf-8")

    assert result["decision"] == "WAITING_FOR_HUMAN_APPROVAL"
    assert "AI Software Factory Report" in report
    assert "Production deployed: false" in report


def test_workflow_execution(monkeypatch, tmp_path):
    runner = load_module("factory_runner", FACTORY_DIR / "run_ai_factory.py")

    def fake_run_command(args, timeout=900):
        if any(str(arg).endswith("run_phase_review.py") for arg in args):
            stdout = json.dumps({"status": "WAITING_HUMAN_APPROVAL", "decision": "PASS"})
        else:
            stdout = json.dumps({"status": "PASS"})
        return {
            "command": " ".join(str(arg) for arg in args),
            "returncode": 0,
            "duration_seconds": 0.01,
            "stdout_tail": stdout,
            "stderr_tail": "",
            "status": "PASS",
        }

    def fake_evidence_package(phase="13.8", command_results=None, correction_result=None, output_path=None):
        return {
            "phase": phase,
            "tests": command_results or [],
            "factory_correction": correction_result or {},
            "safety": {
                "production_deployed": False,
                "code_auto_merged": False,
                "human_approval_required": True,
            },
        }

    def fake_final_report(evidence_path=None, output_path=None):
        return {
            "output": "docs/reviews/AI_SOFTWARE_FACTORY_REPORT.md",
            "decision": "WAITING_FOR_HUMAN_APPROVAL",
        }

    monkeypatch.setattr(runner, "run_command", fake_run_command)
    monkeypatch.setattr(runner, "build_evidence_package", fake_evidence_package)
    monkeypatch.setattr(runner, "generate_final_report", fake_final_report)
    monkeypatch.setattr(runner, "DEFAULT_RESULT", tmp_path / "factory_result.json")
    result = runner.run_factory(phase="13.8")

    assert result["status"] == "WAITING_HUMAN_APPROVAL"
    assert result["correction"]["status"] == "NOT_REQUIRED"
    assert result["safety"]["production_deployed"] is False
    assert result["safety"]["code_auto_merged"] is False


def test_safety_boundaries_are_documented():
    architecture = (DOCS / "ai-factory" / "AI_SOFTWARE_FACTORY_ARCHITECTURE.md").read_text(encoding="utf-8")
    guide = (DOCS / "ai-factory" / "AI_SOFTWARE_FACTORY_GUIDE.md").read_text(encoding="utf-8")
    summary = (DOCS / "reviews" / "AI_SOFTWARE_FACTORY_FINAL_SUMMARY.md").read_text(encoding="utf-8")

    combined = f"{architecture}\n{guide}\n{summary}".lower()
    assert "does not deploy production" in combined
    assert "does not merge" in combined
    assert "human approval" in combined
    assert "hide failed tests" in combined
