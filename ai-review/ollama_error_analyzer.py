"""Analyze captured test errors with local Ollama or safe fallback."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ollama_phase_reviewer import ask_ollama


DEFAULT_ERROR_REPORT = PROJECT_ROOT / "ai-review" / "results" / "error_report.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "ai-review" / "results" / "error_analysis.json"
DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def utc_now():
    """Return an ISO timestamp for analysis evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path):
    """Load JSON if available."""
    target = Path(path)
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def build_prompt(error_report):
    """Build compact local AI prompt from error evidence."""
    return f"""
You are a local AI error analyzer for mecprecision-vietnam.

Rules:
- Analyze errors only.
- Do not modify code.
- Do not approve production.
- Do not hide failed tests.
- Human review is required.

Error report:
{json.dumps(error_report, indent=2, ensure_ascii=False)[:9000]}

Return JSON-like content:
problem:
root_cause:
suggested_fix:
priority: low | medium | high
validation:
""".strip()


def fallback_analysis(error_report):
    """Create deterministic analysis when Ollama is unavailable."""
    failed_tests = error_report.get("failed_tests") or []
    stack_trace = error_report.get("stack_trace") or error_report.get("stderr_tail") or ""
    if error_report.get("status") == "NO_ERROR":
        return {
            "problem": "No failing test was detected.",
            "root_cause": "The command completed successfully.",
            "suggested_fix": "No correction task is required.",
            "priority": "low",
        }
    return {
        "problem": f"Test command failed with return code {error_report.get('returncode')}.",
        "root_cause": f"Review failed tests: {failed_tests or 'not detected'}; inspect stack trace tail.",
        "suggested_fix": "Open the failing test and implementation, fix the smallest relevant issue, then rerun the same validation command.",
        "priority": "high" if failed_tests or stack_trace else "medium",
    }


def analyze_error(error_report_path=DEFAULT_ERROR_REPORT, output_path=None, ollama_url=DEFAULT_OLLAMA_URL, model=DEFAULT_MODEL):
    """Analyze error report and write JSON result."""
    error_report = load_json(error_report_path)
    ollama_result = {"available": False, "response": "", "error": "", "models": [], "model_available": False}
    analysis = fallback_analysis(error_report)

    if error_report.get("status") == "ERROR_CAPTURED":
        ollama_result = ask_ollama(build_prompt(error_report), model=model, ollama_url=ollama_url, timeout=60)
        if ollama_result.get("available") and ollama_result.get("response"):
            analysis["ai_response"] = ollama_result["response"]

    result = {
        "phase": "13.6",
        "created_at": utc_now(),
        "status": "ANALYSIS_COMPLETE",
        "problem": analysis["problem"],
        "root_cause": analysis["root_cause"],
        "suggested_fix": analysis["suggested_fix"],
        "priority": analysis["priority"],
        "ai_response": analysis.get("ai_response", ""),
        "ollama": {
            "url": ollama_url,
            "model": model,
            "available": ollama_result.get("available"),
            "model_available": ollama_result.get("model_available"),
            "error": ollama_result.get("error") or "",
        },
        "safety": {
            "code_modified_by_ai": False,
            "production_modified": False,
            "tests_skipped": False,
            "human_approval_required": True,
        },
    }

    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main():
    """Command-line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Analyze captured test error.")
    parser.add_argument("--error-report", default=str(DEFAULT_ERROR_REPORT))
    parser.add_argument("--output", default=None)
    parser.add_argument("--url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    result = analyze_error(
        error_report_path=args.error_report,
        output_path=args.output,
        ollama_url=args.url,
        model=args.model,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
