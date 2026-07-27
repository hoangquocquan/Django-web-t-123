"""Generate an AI-assisted phase review report with Ollama.

The reviewer is advisory only. It never approves production and it exits
successfully when Ollama is unavailable by generating a warning report.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VALIDATION = PROJECT_ROOT / "docs" / "ai-devops" / "phase_validation_result.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "ai-devops" / "AI_PHASE_REVIEW_REPORT.md"
DEFAULT_PROMPT = PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_12.4_AI_DEVOPS_CONTROL_CENTER.md"
DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")


def utc_now():
    """Return a timestamp for AI review evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_file(path, limit=8000):
    """Read a text file with a maximum size for prompt safety."""
    target = Path(path)
    if not target.exists():
        return ""
    return target.read_text(encoding="utf-8", errors="replace")[:limit]


def run_git(args):
    """Run a read-only Git command for review context."""
    completed = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def load_validation(path):
    """Load validator JSON if available."""
    target = Path(path)
    if not target.exists():
        return {"status": "MISSING", "missing": ["phase_validation_result.json"], "warnings": []}
    return json.loads(target.read_text(encoding="utf-8"))


def build_review_prompt(phase, validation, test_result):
    """Build the local AI review prompt."""
    prompt_text = read_file(DEFAULT_PROMPT)
    changed_files = run_git(["diff", "--name-only", "HEAD"])
    staged_files = run_git(["diff", "--cached", "--name-only"])
    latest_commit = run_git(["log", "-1", "--oneline"])

    return f"""
You are an AI phase reviewer for the mecprecision-vietnam migration.

Rules:
- Never approve production.
- Never deploy anything.
- Human architecture approval is required.
- Detect missing documentation, missing tests, security risks, and rollback gaps.

Phase: {phase}
Latest commit: {latest_commit}
Changed files:
{changed_files or staged_files or "No uncommitted changed files detected."}

Validation result:
{json.dumps(validation, indent=2, ensure_ascii=False)}

Test result:
{test_result}

Phase requirement:
{prompt_text}

Return a concise review with:
1. decision: PASS, PASS_WITH_WARNING, or BLOCKED
2. key risks
3. missing items
4. production safety confirmation
5. human review reminder
""".strip()


def ask_ollama(prompt, model=DEFAULT_MODEL, ollama_url=DEFAULT_OLLAMA_URL, timeout=5):
    """Call Ollama local API and return response text or an error."""
    endpoint = ollama_url.rstrip("/") + "/api/generate"
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    request = urllib.request.Request(endpoint, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
            return {"available": True, "response": body.get("response", "").strip(), "error": ""}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"available": False, "response": "", "error": str(exc)}


def decide(validation, ollama_result):
    """Choose an advisory decision from validation and Ollama state."""
    if validation.get("status") != "PASS":
        return "BLOCKED"
    if validation.get("warnings") or not ollama_result.get("available"):
        return "PASS_WITH_WARNING"
    return "PASS"


def render_report(phase, validation, ollama_result, decision):
    """Render the AI phase review report as Markdown."""
    ai_text = ollama_result.get("response") or "Ollama is not available. Local validation passed, but AI review is limited."
    return f"""# AI Phase Review Report

## Phase

{phase}

## Created At

{utc_now()}

## Decision

{decision}

## Ollama Integration

- URL: {DEFAULT_OLLAMA_URL}
- Model: {DEFAULT_MODEL}
- Available: {ollama_result.get("available")}
- Error: {ollama_result.get("error") or "None"}

## Validator Status

- Status: {validation.get("status")}
- Missing: {validation.get("missing", [])}
- Warnings: {validation.get("warnings", [])}

## AI Review

{ai_text}

## Production Safety

- Auto deploy: false
- Auto approve production: false
- Human review required: true

## Final Note

This report is advisory. It does not replace architecture review and does not
authorize production deployment.
"""


def generate_review(phase="12.4", validation_path=None, output_path=None, test_result="Not provided"):
    """Generate the AI-assisted review report."""
    validation = load_validation(validation_path or DEFAULT_VALIDATION)
    prompt = build_review_prompt(phase, validation, test_result)
    ollama_result = ask_ollama(prompt)
    decision = decide(validation, ollama_result)
    report = render_report(phase, validation, ollama_result, decision)

    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    return {
        "phase": phase,
        "decision": decision,
        "ollama_available": ollama_result.get("available"),
        "output": str(output),
        "auto_deploy": False,
        "auto_approve_production": False,
        "human_review_required": True,
    }


def main():
    """Command-line entrypoint."""
    parser = argparse.ArgumentParser(description="Generate an Ollama-assisted phase review report.")
    parser.add_argument("--phase", default="12.4")
    parser.add_argument("--validation", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--test-result", default="Manual test result not supplied to reviewer script.")
    args = parser.parse_args()

    result = generate_review(
        phase=args.phase,
        validation_path=args.validation,
        output_path=args.output,
        test_result=args.test_result,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

