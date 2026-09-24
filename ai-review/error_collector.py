"""Collect test failure details for the AI self correction loop."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "ai-review" / "results" / "error_report.json"


def utc_now():
    """Return an ISO timestamp for error evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_git(args):
    """Run a read-only Git command."""
    completed = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip()


def normalize_command(command):
    """Convert CLI command text into a safe command list."""
    if isinstance(command, list):
        return command
    if command:
        return str(command).split()
    return [sys.executable, "-m", "pytest"]


def run_test_command(command, timeout=300):
    """Run a test command and capture stdout/stderr."""
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            normalize_command(command),
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
        "command": " ".join(normalize_command(command)),
        "returncode": returncode,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "stdout": stdout,
        "stderr": stderr,
    }


def extract_failed_tests(output):
    """Extract likely failed pytest test names from output."""
    text = str(output or "")
    failed = []
    for match in re.findall(r"FAILED\s+([^\s]+)", text):
        failed.append(match)
    for match in re.findall(r"_{5,}\s+([^\n]+)\s+_{5,}", text):
        if "::" in match:
            failed.append(match.strip())
    return sorted(set(failed))


def extract_stack_trace(output, limit=12000):
    """Keep the most useful tail of the failure output."""
    text = str(output or "")
    markers = ["Traceback", "E   ", "FAILED"]
    positions = [text.find(marker) for marker in markers if text.find(marker) >= 0]
    if positions:
        text = text[min(positions) :]
    return text[-limit:]


def collect_error(command=None, output_path=None, precomputed_result=None):
    """Collect error information from a command result and write JSON evidence."""
    result = precomputed_result or run_test_command(command)
    combined = f"{result.get('stdout', '')}\n{result.get('stderr', '')}"
    report = {
        "phase": "13.6",
        "created_at": utc_now(),
        "status": "NO_ERROR" if result.get("returncode") == 0 else "ERROR_CAPTURED",
        "command": result.get("command", " ".join(normalize_command(command))),
        "returncode": result.get("returncode"),
        "duration_seconds": result.get("duration_seconds", 0),
        "failed_tests": extract_failed_tests(combined),
        "stack_trace": extract_stack_trace(combined),
        "stdout_tail": str(result.get("stdout", ""))[-12000:],
        "stderr_tail": str(result.get("stderr", ""))[-12000:],
        "changed_files": run_git(["status", "--short"]).splitlines(),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "cwd": str(PROJECT_ROOT),
            "ci": os.getenv("CI", "false"),
        },
        "safety": {
            "production_modified": False,
            "tests_skipped": False,
            "fake_pass_created": False,
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

    parser = argparse.ArgumentParser(description="Collect test error evidence.")
    parser.add_argument("--command", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    result = collect_error(command=args.command, output_path=args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
