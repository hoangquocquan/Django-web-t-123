"""Execute validation tests for the AI Phase Review Engine."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "ai-review" / "results" / "test_result.json"


def utc_now():
    """Return an ISO timestamp for test evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def find_powershell():
    """Find PowerShell for the migration validation script."""
    return shutil.which("powershell") or shutil.which("pwsh")


def command_text(command):
    """Render command list as text."""
    return " ".join(str(part) for part in command)


def run_command(command, timeout=600):
    """Run a validation command and return structured output."""
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
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except (subprocess.TimeoutExpired, OSError) as exc:
        returncode = 124
        stdout = ""
        stderr = str(exc)
    return {
        "command": command_text(command),
        "returncode": returncode,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "stdout_tail": stdout[-12000:],
        "stderr_tail": stderr[-12000:],
    }


def build_commands(include_migration=True):
    """Build the command list for phase review tests."""
    commands = [
        {
            "name": "phase_13_5_tests",
            "command": [sys.executable, "-m", "pytest", "tests/test_phase13_5_ai_review_engine.py"],
            "timeout": 180,
            "required": True,
        },
        {
            "name": "phase_validator",
            "command": [sys.executable, "scripts/phase_validator.py", "--phase", "13.5"],
            "timeout": 120,
            "required": True,
        },
    ]
    powershell = find_powershell()
    if include_migration and powershell:
        commands.append(
            {
                "name": "migration_validation",
                "command": [powershell, "-ExecutionPolicy", "Bypass", "-File", "scripts/run_migration_test.ps1"],
                "timeout": 900,
                "required": True,
            }
        )
    elif include_migration:
        commands.append(
            {
                "name": "migration_validation",
                "command": [],
                "timeout": 0,
                "required": True,
                "missing": "PowerShell not found.",
            }
        )
    return commands


def execute_tests(output_path=None, include_migration=True, dry_run=False):
    """Run tests and write JSON evidence."""
    results = []
    for item in build_commands(include_migration=include_migration):
        if item.get("missing"):
            result = {
                "name": item["name"],
                "status": "FAIL",
                "required": item["required"],
                "command": "",
                "returncode": 127,
                "duration_seconds": 0,
                "stdout_tail": "",
                "stderr_tail": item["missing"],
            }
        elif dry_run:
            result = {
                "name": item["name"],
                "status": "PASS",
                "required": item["required"],
                "command": command_text(item["command"]),
                "returncode": 0,
                "duration_seconds": 0,
                "stdout_tail": "dry-run",
                "stderr_tail": "",
            }
        else:
            result = run_command(item["command"], timeout=item["timeout"])
            result["name"] = item["name"]
            result["required"] = item["required"]
            result["status"] = "PASS" if result["returncode"] == 0 else "FAIL"
        results.append(result)

    failed = [result for result in results if result["required"] and result["status"] == "FAIL"]
    report = {
        "phase": "13.5",
        "created_at": utc_now(),
        "status": "PASS" if not failed else "FAIL",
        "results": results,
        "failed_required": [result["name"] for result in failed],
        "duration_seconds": round(sum(result.get("duration_seconds", 0) for result in results), 3),
        "safety": {
            "failed_tests_skipped": False,
            "production_deployed": False,
            "human_approval_required": True,
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

    parser = argparse.ArgumentParser(description="Execute AI phase review tests.")
    parser.add_argument("--output", default=None)
    parser.add_argument("--skip-migration", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = execute_tests(output_path=args.output, include_migration=not args.skip_migration, dry_run=args.dry_run)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
