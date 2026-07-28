"""Control the AI-assisted self correction retry loop.

The controller runs tests and creates fix instructions when they fail. It does
not apply fixes automatically; Codex or a developer must apply the generated
task and rerun validation.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ENGINE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ENGINE_DIR.parents[0]
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from codex_fix_generator import generate_fix_task
from error_collector import collect_error, normalize_command
from ollama_error_analyzer import analyze_error


DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "reviews" / "PHASE_13.6_SELF_CORRECTION_REPORT.md"
DEFAULT_RESULT = PROJECT_ROOT / "ai-review" / "results" / "self_correction_result.json"
MAX_RETRIES = 3


def utc_now():
    """Return an ISO timestamp for retry evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_command(command, timeout=300):
    """Run one test command and capture output."""
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


def render_report(result):
    """Render the Phase 13.6 Markdown report."""
    last_error = result.get("last_error", {})
    analysis = result.get("analysis", {})
    return f"""# Phase 13.6 Self Correction Report

## Test Result

Status:

```text
{result.get("status")}
```

Command:

```text
{result.get("command")}
```

## Error Analysis

Problem:

{analysis.get("problem", "No error detected.")}

Root cause:

{analysis.get("root_cause", "No root cause required.")}

## Fix Suggestion

{analysis.get("suggested_fix", "No fix task required.")}

Generated task:

```text
{result.get("fix_task", "")}
```

## Retry Count

Current retry count:

```text
{result.get("retry_count")}
```

Maximum retry count:

```text
{result.get("max_retries")}
```

Failed tests:

```text
{last_error.get("failed_tests", [])}
```

## Final Decision

```text
{result.get("final_decision")}
```

## Safety

- Production modified: false
- Tests skipped: false
- Fake pass created: false
- Code modified automatically by AI: false
- Human approval required: true
"""


def run_self_correction(command=None, max_retries=MAX_RETRIES, output_path=None, result_path=None, stop_after_fix_task=True):
    """Run the self-correction loop and write evidence/report."""
    if max_retries > MAX_RETRIES:
        max_retries = MAX_RETRIES

    selected_command = command or [sys.executable, "-m", "pytest", "tests/test_phase13_6_self_correction.py"]
    result_output = Path(result_path or DEFAULT_RESULT)
    report_output = Path(output_path or DEFAULT_OUTPUT)
    artifact_dir = result_output.parent
    error_output = artifact_dir / "error_report.json"
    analysis_output = artifact_dir / "error_analysis.json"
    fix_task_output = (
        PROJECT_ROOT / "docs" / "codex-prompts" / "AUTO_FIX_TASK.md"
        if result_path is None
        else artifact_dir / "AUTO_FIX_TASK.md"
    )
    attempts = []
    last_error = {}
    analysis = {}
    fix_task = ""
    status = "PASS"

    for attempt in range(1, max_retries + 1):
        command_result = run_command(selected_command)
        attempts.append(
            {
                "attempt": attempt,
                "returncode": command_result["returncode"],
                "duration_seconds": command_result["duration_seconds"],
            }
        )
        if command_result["returncode"] == 0:
            status = "PASS"
            break

        status = "BLOCKED"
        last_error = collect_error(precomputed_result=command_result, output_path=error_output)
        analysis = analyze_error(error_report_path=error_output, output_path=analysis_output)
        fix_result = generate_fix_task(error_report_path=error_output, analysis_path=analysis_output, output_path=fix_task_output)
        fix_task = fix_result["output"]
        if stop_after_fix_task:
            break
    else:
        status = "BLOCKED"

    final_decision = "PASS" if status == "PASS" else "BLOCKED"
    result = {
        "phase": "13.6",
        "created_at": utc_now(),
        "status": status,
        "final_decision": final_decision,
        "command": " ".join(normalize_command(selected_command)),
        "retry_count": len(attempts),
        "max_retries": max_retries,
        "attempts": attempts,
        "last_error": last_error,
        "analysis": analysis,
        "fix_task": fix_task,
        "safety": {
            "production_modified": False,
            "tests_skipped": False,
            "fake_pass_created": False,
            "code_modified_by_ai": False,
            "human_approval_required": True,
        },
    }

    result_output.parent.mkdir(parents=True, exist_ok=True)
    result_output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    report_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.write_text(render_report(result), encoding="utf-8")
    return result


def main():
    """Command-line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run AI self correction loop.")
    parser.add_argument("--command", default=None)
    parser.add_argument("--max-retries", type=int, default=MAX_RETRIES)
    parser.add_argument("--continue-after-fix-task", action="store_true")
    parser.add_argument("--output", default=None)
    parser.add_argument("--result", default=None)
    args = parser.parse_args()

    result = run_self_correction(
        command=args.command,
        max_retries=args.max_retries,
        output_path=args.output,
        result_path=args.result,
        stop_after_fix_task=not args.continue_after_fix_task,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in {"PASS", "BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
