"""Run the Phase 13.2 automated test pipeline.

The runner turns the manual validation checklist into repeatable evidence for
local use and CI. It never deploys production and never creates real secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "cicd" / "test_pipeline_result.json"
CONFIG_PATH = PROJECT_ROOT / "ci" / "test_pipeline_config.yml"


def utc_now():
    """Return an ISO timestamp for pipeline evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def find_powershell():
    """Find a PowerShell executable that can run the migration test script."""
    return shutil.which("powershell") or shutil.which("pwsh")


def command_to_text(command):
    """Render a command list for evidence."""
    return " ".join(str(part) for part in command)


def trim_output(value, limit=12000):
    """Keep report files readable by storing the tail of long command output."""
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[-limit:]


def parse_test_counts(output):
    """Extract rough pytest-style pass/fail/warning counts from command output."""
    text = str(output or "")
    passed = sum(int(match) for match in re.findall(r"(\d+)\s+passed", text))
    failed = sum(int(match) for match in re.findall(r"(\d+)\s+failed", text))
    warnings = sum(int(match) for match in re.findall(r"(\d+)\s+warnings?", text))
    return {"passed": passed, "failed": failed, "warnings": warnings}


def run_command(command, timeout=300, env=None):
    """Run one pipeline command and return structured evidence."""
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except (subprocess.TimeoutExpired, OSError) as exc:
        returncode = 124
        stdout = ""
        stderr = str(exc)

    duration = round(time.perf_counter() - started, 3)
    counts = parse_test_counts(stdout + "\n" + stderr)
    return {
        "command": command_to_text(command),
        "returncode": returncode,
        "duration_seconds": duration,
        "stdout_tail": trim_output(stdout),
        "stderr_tail": trim_output(stderr),
        "passed_tests": counts["passed"],
        "failed_tests": counts["failed"],
        "warnings": counts["warnings"],
    }


def build_stages():
    """Create the CI-ready stage list.

    The YAML config documents the same stages for humans and CI. The Python
    runner keeps commands as lists to avoid fragile shell parsing.
    """
    powershell = find_powershell()
    migration_command = (
        [powershell, "-ExecutionPolicy", "Bypass", "-File", "scripts/run_migration_test.ps1"]
        if powershell
        else None
    )
    return [
        {
            "name": "dependency_check",
            "required": True,
            "timeout_seconds": 60,
            "command": [sys.executable, "-c", "import django, pytest; print('dependencies ok')"],
        },
        {
            "name": "lint_check",
            "required": False,
            "timeout_seconds": 120,
            "command": ["ruff", "check", "."],
            "skip_if_missing": "ruff",
        },
        {
            "name": "unit_tests",
            "required": True,
            "timeout_seconds": 120,
            "command": [sys.executable, "-m", "pytest", "tests/test_phase13_2_test_pipeline.py"],
        },
        {
            "name": "integration_tests",
            "required": True,
            "timeout_seconds": 180,
            "command": [sys.executable, "-m", "pytest", "tests/test_phase13_1_docker_build.py"],
        },
        {
            "name": "security_tests",
            "required": True,
            "timeout_seconds": 180,
            "command": [sys.executable, "-m", "pytest", "tests/test_phase12_1_security.py"],
        },
        {
            "name": "migration_tests",
            "required": True,
            "timeout_seconds": 600,
            "command": migration_command,
        },
    ]


def evaluate_stage(stage, dry_run=False):
    """Run or simulate one stage and return its evidence."""
    command = stage.get("command")
    if not command:
        return {
            "name": stage["name"],
            "status": "FAIL" if stage["required"] else "WARN",
            "required": stage["required"],
            "warning": "Required command executable was not found.",
            "command": "",
            "returncode": 127,
            "duration_seconds": 0,
            "passed_tests": 0,
            "failed_tests": 1 if stage["required"] else 0,
            "warnings": 1,
        }

    missing_tool = stage.get("skip_if_missing")
    if missing_tool and not shutil.which(missing_tool):
        return {
            "name": stage["name"],
            "status": "WARN",
            "required": stage["required"],
            "warning": f"Optional tool not installed: {missing_tool}",
            "command": command_to_text(command),
            "returncode": None,
            "duration_seconds": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "warnings": 1,
        }

    if dry_run:
        return {
            "name": stage["name"],
            "status": "PASS",
            "required": stage["required"],
            "warning": "",
            "command": command_to_text(command),
            "returncode": 0,
            "duration_seconds": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "warnings": 0,
        }

    env = os.environ.copy()
    env.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
    env.setdefault("PYTHONUNBUFFERED", "1")
    result = run_command(command, timeout=stage["timeout_seconds"], env=env)
    status = "PASS" if result["returncode"] == 0 else "FAIL"
    return {
        "name": stage["name"],
        "status": status,
        "required": stage["required"],
        "warning": "",
        **result,
    }


def summarize(stages):
    """Calculate overall pipeline totals."""
    failed_required = [stage for stage in stages if stage["required"] and stage["status"] == "FAIL"]
    total_duration = round(sum(stage.get("duration_seconds", 0) for stage in stages), 3)
    return {
        "status": "TEST_PIPELINE_COMPLETE" if not failed_required else "TEST_PIPELINE_BLOCKED",
        "duration_seconds": total_duration,
        "passed_tests": sum(stage.get("passed_tests", 0) for stage in stages),
        "failed_tests": sum(stage.get("failed_tests", 0) for stage in stages),
        "warnings": sum(stage.get("warnings", 0) for stage in stages),
        "failed_required_stages": [stage["name"] for stage in failed_required],
    }


def run_pipeline(output_path=None, dry_run=False):
    """Run all pipeline stages and write JSON evidence."""
    stages = [evaluate_stage(stage, dry_run=dry_run) for stage in build_stages()]
    summary = summarize(stages)
    report = {
        "phase": "13.2",
        "created_at": utc_now(),
        "config": str(CONFIG_PATH),
        "summary": summary,
        "stages": stages,
        "safety": {
            "production_deployed": False,
            "real_ci_secrets_created": False,
            "failed_tests_bypassed": False,
            "external_push": False,
        },
    }

    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main():
    """Command-line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run Phase 13.2 automated test pipeline.")
    parser.add_argument("--output", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    report = run_pipeline(output_path=args.output, dry_run=args.dry_run)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["summary"]["status"] == "TEST_PIPELINE_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
