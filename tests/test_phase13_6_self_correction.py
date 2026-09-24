import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = PROJECT_ROOT / "ai-review"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from codex_fix_generator import generate_fix_task
from error_collector import collect_error
from ollama_error_analyzer import analyze_error
from retry_controller import run_self_correction


DOCS = PROJECT_ROOT / "docs"


def read(path):
    return Path(path).read_text(encoding="utf-8")


def test_self_correction_files_exist():
    required = [
        DOCS / "codex-prompts" / "PHASE_13.6_AI_SELF_CORRECTION_LOOP.md",
        ENGINE_DIR / "error_collector.py",
        ENGINE_DIR / "ollama_error_analyzer.py",
        ENGINE_DIR / "codex_fix_generator.py",
        ENGINE_DIR / "retry_controller.py",
        DOCS / "ai-review" / "SELF_CORRECTION_SECURITY.md",
        DOCS / "reviews" / "PHASE_13.6_SELF_CORRECTION_REPORT.md",
    ]

    for path in required:
        assert path.exists(), f"Missing self correction artifact: {path}"
        assert path.stat().st_size > 0


def test_error_capture_from_failed_command(tmp_path):
    command_result = {
        "command": "pytest fake",
        "returncode": 1,
        "duration_seconds": 0.1,
        "stdout": "FAILED tests/test_demo.py::test_example - AssertionError",
        "stderr": "E   AssertionError: expected true",
    }

    report = collect_error(precomputed_result=command_result, output_path=tmp_path / "error_report.json")

    assert report["status"] == "ERROR_CAPTURED"
    assert "tests/test_demo.py::test_example" in report["failed_tests"]
    assert report["safety"]["tests_skipped"] is False
    assert report["safety"]["fake_pass_created"] is False


def test_ollama_unavailable_handling(tmp_path):
    error_report = tmp_path / "error_report.json"
    error_report.write_text(
        json.dumps(
            {
                "status": "ERROR_CAPTURED",
                "returncode": 1,
                "failed_tests": ["tests/test_demo.py::test_example"],
                "stack_trace": "AssertionError",
            }
        ),
        encoding="utf-8",
    )

    analysis = analyze_error(
        error_report_path=error_report,
        output_path=tmp_path / "error_analysis.json",
        ollama_url="http://127.0.0.1:1",
    )

    assert analysis["status"] == "ANALYSIS_COMPLETE"
    assert analysis["priority"] == "high"
    assert analysis["safety"]["code_modified_by_ai"] is False
    assert analysis["safety"]["human_approval_required"] is True


def test_fix_task_generation(tmp_path):
    error_report = tmp_path / "error_report.json"
    analysis_path = tmp_path / "error_analysis.json"
    output_path = tmp_path / "AUTO_FIX_TASK.md"

    error_report.write_text(json.dumps({"command": "pytest", "returncode": 1, "failed_tests": ["test_x"]}), encoding="utf-8")
    analysis_path.write_text(
        json.dumps({"root_cause": "Demo cause", "suggested_fix": "Demo fix", "priority": "medium"}),
        encoding="utf-8",
    )

    result = generate_fix_task(error_report_path=error_report, analysis_path=analysis_path, output_path=output_path)

    assert result["status"] == "FIX_TASK_GENERATED"
    assert result["code_modified_by_ai"] is False
    assert "Demo fix" in output_path.read_text(encoding="utf-8")


def test_retry_limit_and_blocked_result(tmp_path):
    command = [sys.executable, "-c", "import sys; print('FAILED tests/test_demo.py::test_example'); sys.exit(1)"]
    result = run_self_correction(
        command=command,
        max_retries=2,
        result_path=tmp_path / "self_correction_result.json",
        output_path=tmp_path / "PHASE_13.6_SELF_CORRECTION_REPORT.md",
        stop_after_fix_task=False,
    )

    assert result["status"] == "BLOCKED"
    assert result["retry_count"] == 2
    assert result["max_retries"] == 2
    assert result["safety"]["fake_pass_created"] is False
    assert result["safety"]["code_modified_by_ai"] is False


def test_successful_retry_controller(tmp_path):
    command = [sys.executable, "-c", "print('ok')"]
    result = run_self_correction(
        command=command,
        max_retries=3,
        result_path=tmp_path / "self_correction_result.json",
        output_path=tmp_path / "PHASE_13.6_SELF_CORRECTION_REPORT.md",
    )

    assert result["status"] == "PASS"
    assert result["retry_count"] == 1
    assert result["final_decision"] == "PASS"


def test_safety_rules_documented():
    content = read(DOCS / "ai-review" / "SELF_CORRECTION_SECURITY.md")

    assert "Maximum Retry Limit" in content
    assert "Human approval is required" in content
    assert "No Production Modification" in content
    assert "No Fake PASS" in content
