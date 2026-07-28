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
    },
    "13.4": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_13.4_DEPLOYMENT_AUTOMATION.md",
        "documents": [
            PROJECT_ROOT / "docs" / "deployment" / "DEPLOYMENT_ARCHITECTURE.md",
            PROJECT_ROOT / "docs" / "deployment" / "DEPLOYMENT_RUNBOOK.md",
            PROJECT_ROOT / "docs" / "deployment" / "DEPLOYMENT_SECURITY.md",
            PROJECT_ROOT / "docs" / "deployment" / "deployment_result.json",
            PROJECT_ROOT / "docs" / "deployment" / "health_result.json",
            PROJECT_ROOT / "docs" / "deployment" / "rollback_result.json",
            PROJECT_ROOT / "docs" / "n8n" / "N8N_DEPLOYMENT_WORKFLOW.md",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_13.4_DEPLOYMENT_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase13_4_deployment.py",
        ],
        "expected_tag": "phase-13.4-deployment-ready",
    },
    "13.5": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_13.5_AI_PHASE_REVIEW_ENGINE.md",
        "documents": [
            PROJECT_ROOT / "docs" / "ai-review" / "AI_PHASE_REVIEW_ENGINE_ARCHITECTURE.md",
            PROJECT_ROOT / "ai-review" / "config.yml",
            PROJECT_ROOT / "ai-review" / "evidence_collector.py",
            PROJECT_ROOT / "ai-review" / "requirement_validator.py",
            PROJECT_ROOT / "ai-review" / "test_executor.py",
            PROJECT_ROOT / "ai-review" / "ollama_phase_reviewer.py",
            PROJECT_ROOT / "ai-review" / "report_generator.py",
            PROJECT_ROOT / "ai-review" / "run_phase_review.py",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase13_5_ai_review_engine.py",
        ],
        "expected_tag": "phase-13.5-ai-review-ready",
    },
    "13.6": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_13.6_AI_SELF_CORRECTION_LOOP.md",
        "documents": [
            PROJECT_ROOT / "ai-review" / "error_collector.py",
            PROJECT_ROOT / "ai-review" / "ollama_error_analyzer.py",
            PROJECT_ROOT / "ai-review" / "codex_fix_generator.py",
            PROJECT_ROOT / "ai-review" / "retry_controller.py",
            PROJECT_ROOT / "docs" / "ai-review" / "SELF_CORRECTION_SECURITY.md",
            PROJECT_ROOT / "docs" / "codex-prompts" / "AUTO_FIX_TASK.md",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_13.6_SELF_CORRECTION_REPORT.md",
            PROJECT_ROOT / "ai-review" / "results" / "error_report.json",
            PROJECT_ROOT / "ai-review" / "results" / "error_analysis.json",
            PROJECT_ROOT / "ai-review" / "results" / "self_correction_result.json",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase13_6_self_correction.py",
        ],
        "expected_tag": "phase-13.6-self-correction-ready",
    },
    "13.7": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_13.7_N8N_REAL_AUTOMATION_CONTROLLER.md",
        "documents": [
            PROJECT_ROOT / "docs" / "n8n" / "N8N_REAL_AUTOMATION_ARCHITECTURE.md",
            PROJECT_ROOT / "n8n" / "workflows" / "phase_automation_controller.json",
            PROJECT_ROOT / "n8n" / "config" / "n8n_phase_controller.yml",
            PROJECT_ROOT / "scripts" / "n8n_phase_trigger.py",
            PROJECT_ROOT / "docs" / "n8n" / "N8N_NOTIFICATION_DESIGN.md",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_13.7_N8N_AUTOMATION_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase13_7_n8n_controller.py",
        ],
        "expected_tag": "phase-13.7-n8n-controller-ready",
    },
    "13.8": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_13.8_AI_SOFTWARE_FACTORY_FINAL_INTEGRATION.md",
        "documents": [
            PROJECT_ROOT / "docs" / "ai-factory" / "AI_SOFTWARE_FACTORY_ARCHITECTURE.md",
            PROJECT_ROOT / "docs" / "ai-factory" / "AI_SOFTWARE_FACTORY_GUIDE.md",
            PROJECT_ROOT / "ai-factory" / "run_ai_factory.py",
            PROJECT_ROOT / "ai-factory" / "evidence_builder.py",
            PROJECT_ROOT / "ai-factory" / "final_report_generator.py",
            PROJECT_ROOT / "ai-factory" / "templates" / "phase_requirement_template.md",
            PROJECT_ROOT / "ai-factory" / "templates" / "phase_test_template.md",
            PROJECT_ROOT / "ai-factory" / "templates" / "phase_review_template.md",
            PROJECT_ROOT / "docs" / "reviews" / "AI_SOFTWARE_FACTORY_REPORT.md",
            PROJECT_ROOT / "docs" / "reviews" / "AI_SOFTWARE_FACTORY_FINAL_SUMMARY.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase13_8_ai_factory.py",
        ],
        "expected_tag": "phase-13.8-ai-factory-complete",
    },
    "14.1": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_14.1_DJANGO_OWNERSHIP_MIGRATION.md",
        "documents": [
            PROJECT_ROOT / "docs" / "django-migration" / "PHASE_14.1_DOMAIN_SELECTION.md",
            PROJECT_ROOT / "docs" / "django-migration" / "DJANGO_OWNERSHIP_DESIGN.md",
            PROJECT_ROOT / "docs" / "django-migration" / "MIGRATION_RESULT.md",
            PROJECT_ROOT / "django_backend" / "apps" / "newsletter" / "models.py",
            PROJECT_ROOT / "django_backend" / "apps" / "newsletter" / "services.py",
            PROJECT_ROOT / "django_backend" / "apps" / "newsletter" / "migrations" / "0001_initial.py",
            PROJECT_ROOT / "django_backend" / "apps" / "newsletter" / "migrations" / "0002_import_legacy_subscribers.py",
            PROJECT_ROOT / "django_backend" / "apps" / "api" / "serializers" / "newsletter.py",
            PROJECT_ROOT / "django_backend" / "apps" / "api" / "views" / "newsletter.py",
            PROJECT_ROOT / "ai-factory" / "evidence" / "django_phase14_1.json",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_14.1_DJANGO_OWNERSHIP_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_14.1_DJANGO_OWNERSHIP_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase14_1_django_ownership.py",
        ],
        "expected_tag": "phase-14.1-django-ownership-ready",
    },
    "django-wave-1": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "WAVE_1_DJANGO_FOUNDATION_MIGRATION.md",
        "documents": [
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE1_AUTH_AUDIT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE1_USER_PROFILE_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE1_PERMISSION_REPORT.md",
            PROJECT_ROOT / "django_backend" / "apps" / "foundation" / "models.py",
            PROJECT_ROOT / "django_backend" / "apps" / "foundation" / "services.py",
            PROJECT_ROOT / "django_backend" / "apps" / "foundation" / "migrations" / "0001_initial.py",
            PROJECT_ROOT / "django_backend" / "apps" / "foundation" / "migrations" / "0002_seed_foundation_from_legacy.py",
            PROJECT_ROOT / "django_backend" / "apps" / "api" / "serializers" / "foundation.py",
            PROJECT_ROOT / "django_backend" / "apps" / "api" / "views" / "foundation.py",
            PROJECT_ROOT / "ai-factory" / "evidence" / "django_wave_1.json",
            PROJECT_ROOT / "docs" / "reviews" / "WAVE_1_DJANGO_FOUNDATION_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "WAVE_1_DJANGO_FOUNDATION_FINAL_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_wave1_django_foundation.py",
        ],
        "expected_tag": "wave-1-django-foundation-complete",
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
