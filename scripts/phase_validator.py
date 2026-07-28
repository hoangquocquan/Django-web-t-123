"""Validate migration phase artifacts before AI-assisted review.

The validator reads files and Git metadata only. It does not deploy, approve,
or modify production systems.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "ai-devops" / "phase_validation_result.json"


PHASE_REQUIREMENTS = {
    "12.4": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_12.4_AI_DEVOPS_CONTROL_CENTER.md",
        "documents": [
            PROJECT_ROOT / "docs" / "ai-devops" / "AI_DEVOPS_CONTROL_CENTER_ARCHITECTURE.md",
            PROJECT_ROOT / "docs" / "ai-devops" / "AI_REVIEW_RULES.md",
            PROJECT_ROOT / "docs" / "ai-devops" / "N8N_PHASE_REVIEW_WORKFLOW.md",
            PROJECT_ROOT / "docs" / "ai-devops" / "n8n_phase_review_workflow.json",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_12.4_REVIEW_SUMMARY.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase12_4_ai_devops.py",
        ],
        "expected_tag": "phase-12.4-ai-devops-ready",
    },
    "12.4.1": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_12.4.1_OLLAMA_CONNECTION_VALIDATION.md",
        "documents": [
            PROJECT_ROOT / "docs" / "ai-devops" / "OLLAMA_TEST_PROMPT.md",
            PROJECT_ROOT / "docs" / "ai-devops" / "ollama_environment_check.json",
            PROJECT_ROOT / "docs" / "ai-devops" / "AI_PHASE_REVIEW_REPORT.md",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_12.4.1_OLLAMA_VALIDATION_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase12_4_1_ollama_connection.py",
        ],
        "expected_tag": "phase-12.4.1-ollama-ready",
    },
    "13.2": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_13.2_AUTOMATED_TEST_PIPELINE.md",
        "documents": [
            PROJECT_ROOT / "docs" / "cicd" / "TEST_PIPELINE_ARCHITECTURE.md",
            PROJECT_ROOT / "ci" / "test_pipeline_config.yml",
            PROJECT_ROOT / ".github" / "workflows" / "test_pipeline.yml",
            PROJECT_ROOT / "docs" / "cicd" / "test_pipeline_result.json",
            PROJECT_ROOT / "docs" / "ai-devops" / "TEST_PIPELINE_AI_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_13.2_TEST_PIPELINE_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase13_2_test_pipeline.py",
        ],
        "expected_tag": "phase-13.2-test-pipeline-ready",
    },
    "13.3": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_13.3_N8N_CICD_ORCHESTRATION.md",
        "documents": [
            PROJECT_ROOT / "docs" / "n8n" / "N8N_CICD_ARCHITECTURE.md",
            PROJECT_ROOT / "docs" / "n8n" / "n8n_cicd_pipeline_workflow.json",
            PROJECT_ROOT / "docs" / "n8n" / "N8N_SETUP_GUIDE.md",
            PROJECT_ROOT / "docs" / "n8n" / "N8N_NOTIFICATION_DESIGN.md",
            PROJECT_ROOT / "docs" / "n8n" / "n8n_execution_report.json",
            PROJECT_ROOT / "docs" / "ai-devops" / "N8N_AI_REVIEW_REPORT.md",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_13.3_N8N_CICD_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase13_3_n8n.py",
        ],
        "expected_tag": "phase-13.3-n8n-ready",
    }
}


def utc_now():
    """Return a timestamp for validation evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_git(args):
    """Run a safe read-only Git command and return stripped stdout."""
    completed = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def file_status(path):
    """Return existence and size information for one required file."""
    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def validate_phase(phase="12.4.1", output_path=None):
    """Validate required artifacts for a migration phase."""
    requirements = PHASE_REQUIREMENTS.get(phase)
    missing = []
    warnings = []
    notes = []
    checked_files = []

    if not requirements:
        missing.append(f"No phase requirements configured for {phase}")
        requirements = {"prompt": None, "documents": [], "tests": [], "expected_tag": ""}

    required_paths = []
    if requirements.get("prompt"):
        required_paths.append(requirements["prompt"])
    required_paths.extend(requirements.get("documents", []))
    required_paths.extend(requirements.get("tests", []))

    for path in required_paths:
        status = file_status(path)
        checked_files.append(status)
        if not status["exists"]:
            missing.append(status["path"])
        elif status["size_bytes"] == 0:
            warnings.append(f"Empty file: {status['path']}")

    git_status = run_git(["status", "--short"])
    git_branch = run_git(["branch", "--show-current"])
    tag_result = run_git(["tag", "--list", requirements.get("expected_tag", "")])
    expected_tag = requirements.get("expected_tag", "")
    tag_present = bool(tag_result["stdout"]) if expected_tag else False
    if expected_tag and not tag_present:
        notes.append(f"Expected tag not found yet: {expected_tag}")

    unsafe_status_lines = []
    for line in git_status["stdout"].splitlines():
        if "docs.zip" in line:
            continue
        if "phase_validation_result.json" in line:
            continue
        unsafe_status_lines.append(line)
    if unsafe_status_lines:
        notes.append("Working tree has uncommitted phase changes.")

    status = "PASS" if not missing else "FAIL"
    result = {
        "phase": phase,
        "created_at": utc_now(),
        "status": status,
        "missing": missing,
        "warnings": warnings,
        "notes": notes,
        "checked_files": checked_files,
        "git": {
            "branch": git_branch["stdout"],
            "status_short": git_status["stdout"],
            "expected_tag": expected_tag,
            "expected_tag_present": tag_present,
        },
        "safety": {
            "production_modified": False,
            "auto_deploy": False,
            "auto_approve_production": False,
            "human_review_required": True,
        },
    }

    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main():
    """Command-line entrypoint."""
    parser = argparse.ArgumentParser(description="Validate migration phase artifacts.")
    parser.add_argument("--phase", default="12.4.1")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    result = validate_phase(phase=args.phase, output_path=args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
