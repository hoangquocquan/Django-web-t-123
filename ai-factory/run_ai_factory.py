"""Run the reusable AI Software Factory workflow for one phase."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


FACTORY_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FACTORY_DIR.parents[0]
DEFAULT_RESULT = FACTORY_DIR / "results" / "factory_result.json"

if str(FACTORY_DIR) not in sys.path:
    sys.path.insert(0, str(FACTORY_DIR))

from evidence_builder import build_evidence_package
from final_report_generator import generate_final_report


def utc_now():
    """Return an ISO timestamp for factory execution."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_phase_spec(phase):
    """Load the saved phase prompt so the runner has traceable input."""
    filename = f"PHASE_{phase}_AI_SOFTWARE_FACTORY_FINAL_INTEGRATION.md"
    prompt_path = PROJECT_ROOT / "docs" / "codex-prompts" / filename
    wave_prompt_map = {
        "django-wave-1": "WAVE_1_DJANGO_FOUNDATION_MIGRATION.md",
        "django-wave-2": "WAVE_2_DJANGO_BUSINESS_CORE_MIGRATION.md",
        "django-wave-3": "WAVE_3_DJANGO_TRANSACTION_MIGRATION.md",
        "django-wave-4": "WAVE_4_DJANGO_LEGACY_REDUCTION.md",
        "django-wave-5": "WAVE_5_DJANGO_ADMIN_MIGRATION.md",
        "django-wave-6": "WAVE_6_DJANGO_ADMIN_UI_CUTOVER.md",
    }
    if phase in wave_prompt_map:
        prompt_path = PROJECT_ROOT / "docs" / "codex-prompts" / wave_prompt_map[phase]
    if not prompt_path.exists():
        candidates = sorted((PROJECT_ROOT / "docs" / "codex-prompts").glob(f"PHASE_{phase}*.md"))
        if phase.startswith("django-wave"):
            candidates = sorted((PROJECT_ROOT / "docs" / "codex-prompts").glob("WAVE_*.md"))
        prompt_path = candidates[0] if candidates else prompt_path
    return {
        "phase": phase,
        "path": str(prompt_path.relative_to(PROJECT_ROOT)) if prompt_path.exists() else str(prompt_path),
        "exists": prompt_path.exists(),
        "content_preview": prompt_path.read_text(encoding="utf-8")[:1000] if prompt_path.exists() else "",
    }


def run_command(args, timeout=900):
    """Run one local engineering command and keep visible evidence."""
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            args,
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except (subprocess.TimeoutExpired, OSError) as exc:
        returncode = 124
        stdout = ""
        stderr = str(exc)
    return {
        "command": " ".join(str(arg) for arg in args),
        "returncode": returncode,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "stdout_tail": stdout[-12000:],
        "stderr_tail": stderr[-12000:],
        "status": "PASS" if returncode == 0 else "FAIL",
    }


def prepare_codex_task(phase_spec):
    """Record task preparation; Codex implementation happens in the workspace."""
    return {
        "status": "READY" if phase_spec.get("exists") else "MISSING_PHASE_SPEC",
        "phase_spec": phase_spec.get("path", ""),
        "codex_role": "implementation_agent",
    }


def default_test_command_for_phase(phase):
    """Return the most specific pytest command available for a phase."""
    if phase == "django-wave-1":
        return [sys.executable, "-m", "pytest", "tests/test_wave1_django_foundation.py"]
    if phase == "django-wave-2":
        return [sys.executable, "-m", "pytest", "tests/test_wave2_business_core.py"]
    if phase == "django-wave-3":
        return [sys.executable, "-m", "pytest", "tests/test_wave3_transaction_domain.py"]
    if phase == "django-wave-4":
        return [sys.executable, "-m", "pytest", "tests/test_wave4_legacy_reduction.py"]
    if phase == "django-wave-5":
        return [sys.executable, "-m", "pytest", "tests/test_wave5_admin_migration.py"]
    if phase == "django-wave-6":
        return [sys.executable, "-m", "pytest", "tests/test_wave6_admin_ui.py"]

    normalized_phase = phase.replace(".", "_")
    candidates = [
        PROJECT_ROOT / "tests" / f"test_phase{normalized_phase}_django_ownership.py",
        PROJECT_ROOT / "tests" / f"test_phase{normalized_phase}_ai_factory.py",
    ]
    for candidate in candidates:
        if candidate.exists():
            return [sys.executable, "-m", "pytest", str(candidate.relative_to(PROJECT_ROOT))]
    return [sys.executable, "-m", "pytest", "tests/test_phase13_8_ai_factory.py"]


def run_factory(phase="13.8", test_command=None):
    """Execute validation, tests, correction handling, AI review, and reports."""
    phase_spec = load_phase_spec(phase)
    task_preparation = prepare_codex_task(phase_spec)
    commands = []

    validation = run_command([sys.executable, "scripts/phase_validator.py", "--phase", phase], timeout=120)
    commands.append(validation)

    selected_test_command = test_command or default_test_command_for_phase(phase)
    tests = run_command(selected_test_command, timeout=300)
    commands.append(tests)

    correction = {
        "status": "NOT_REQUIRED",
        "reason": "Tests passed.",
    }
    if tests["returncode"] != 0:
        correction = run_command([sys.executable, "ai-review/retry_controller.py", "--command", " ".join(selected_test_command)], timeout=900)
        commands.append(correction)

    ai_review = run_command([sys.executable, "ai-review/run_phase_review.py", "--phase", phase, "--skip-migration"], timeout=900)
    commands.append(ai_review)

    evidence = build_evidence_package(phase=phase, command_results=commands, correction_result=correction)
    final_report = generate_final_report()

    required_ok = validation["returncode"] == 0 and tests["returncode"] == 0 and ai_review["returncode"] == 0
    status = "AI_SOFTWARE_FACTORY_COMPLETE" if required_ok else "AI_SOFTWARE_FACTORY_BLOCKED"
    result = {
        "phase": phase,
        "created_at": utc_now(),
        "status": status,
        "phase_spec": phase_spec,
        "task_preparation": task_preparation,
        "validation": validation,
        "tests": tests,
        "correction": correction,
        "ai_review": ai_review,
        "evidence_package": "ai-factory/evidence/package.json",
        "final_report": final_report,
        "safety": {
            "production_deployed": False,
            "code_auto_merged": False,
            "human_approval_bypassed": False,
            "failed_tests_hidden": False,
            "human_approval_required": True,
        },
    }

    DEFAULT_RESULT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_RESULT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main():
    """Command-line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run the AI Software Factory workflow.")
    parser.add_argument("--phase", default="13.8")
    parser.add_argument("--wave", default=None)
    args = parser.parse_args()

    result = run_factory(phase=args.wave or args.phase)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "AI_SOFTWARE_FACTORY_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
