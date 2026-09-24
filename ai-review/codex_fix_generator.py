"""Generate a Codex fix task from AI error analysis."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ERROR_REPORT = PROJECT_ROOT / "ai-review" / "results" / "error_report.json"
DEFAULT_ANALYSIS = PROJECT_ROOT / "ai-review" / "results" / "error_analysis.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "codex-prompts" / "AUTO_FIX_TASK.md"


def utc_now():
    """Return an ISO timestamp for task evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path):
    """Load JSON if available."""
    target = Path(path)
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def render_task(error_report, analysis):
    """Render a human/Codex fix task without applying changes."""
    return f"""# AUTO FIX TASK

Generated at: {utc_now()}

## Error

- Command: `{error_report.get("command", "")}`
- Return code: `{error_report.get("returncode")}`
- Failed tests: {error_report.get("failed_tests", [])}

## Root Cause

{analysis.get("root_cause", "Review the captured error report.")}

## Expected Fix

{analysis.get("suggested_fix", "Fix the smallest relevant issue and rerun validation.")}

## Priority

{analysis.get("priority", "medium")}

## Required Validation

Run the same failing command again.

If this task changes code, also run:

```powershell
pytest
```

## Safety Rules

- Do not modify production automatically.
- Do not skip failed tests.
- Do not hide errors.
- Do not create a fake PASS result.
- Human approval is required before final merge.
"""


def generate_fix_task(error_report_path=DEFAULT_ERROR_REPORT, analysis_path=DEFAULT_ANALYSIS, output_path=None):
    """Generate fix task Markdown and return summary."""
    error_report = load_json(error_report_path)
    analysis = load_json(analysis_path)
    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_task(error_report, analysis), encoding="utf-8")
    return {
        "phase": "13.6",
        "status": "FIX_TASK_GENERATED",
        "output": str(output),
        "production_modified": False,
        "code_modified_by_ai": False,
        "human_approval_required": True,
    }


def main():
    """Command-line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Generate Codex fix task.")
    parser.add_argument("--error-report", default=str(DEFAULT_ERROR_REPORT))
    parser.add_argument("--analysis", default=str(DEFAULT_ANALYSIS))
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    result = generate_fix_task(
        error_report_path=args.error_report,
        analysis_path=args.analysis,
        output_path=args.output,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
