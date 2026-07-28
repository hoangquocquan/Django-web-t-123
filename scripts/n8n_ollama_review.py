"""Generate an Ollama advisory review for the n8n CI/CD workflow.

The review is local and advisory. It cannot approve production and it continues
with a warning if Ollama is unavailable.
"""

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

from scripts.ollama_phase_reviewer import ask_ollama, parse_ai_decision


DEFAULT_EXECUTION_REPORT = PROJECT_ROOT / "docs" / "n8n" / "n8n_execution_report.json"
DEFAULT_PIPELINE_RESULT = PROJECT_ROOT / "docs" / "cicd" / "test_pipeline_result.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "ai-devops" / "N8N_AI_REVIEW_REPORT.md"
DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def utc_now():
    """Return an ISO timestamp for AI evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path):
    """Load JSON evidence if it exists."""
    target = Path(path)
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def build_prompt(execution_report, pipeline_result):
    """Build the local Ollama prompt."""
    return f"""
You are a Senior DevOps Reviewer for mecprecision-vietnam.

Review the Phase 13.3 n8n CI/CD orchestration evidence.

Rules:
- Never approve production.
- Never deploy production.
- Never bypass human approval.
- Never replace CI testing.
- AI is advisory only.

n8n execution report:
{json.dumps(execution_report, indent=2, ensure_ascii=False)[:7000]}

test pipeline summary:
{json.dumps(pipeline_result.get("summary", {}), indent=2, ensure_ascii=False)}

Return:
1. decision: PASS, PASS_WITH_WARNING, or BLOCKED
2. orchestration risks
3. security concerns
4. missing approvals
5. production safety confirmation
""".strip()


def decide(execution_report, pipeline_result, ollama_result):
    """Choose advisory decision from evidence and local AI state."""
    if execution_report.get("status") != "N8N_ORCHESTRATION_COMPLETE":
        return "BLOCKED"
    if pipeline_result.get("summary", {}).get("status") != "TEST_PIPELINE_COMPLETE":
        return "BLOCKED"
    if not ollama_result.get("available"):
        return "PASS_WITH_WARNING"
    ai_decision = parse_ai_decision(ollama_result.get("response"))
    if ai_decision == "BLOCKED":
        return "BLOCKED"
    if execution_report.get("mode") == "local_dry_run" and ai_decision == "PASS":
        return "PASS_WITH_WARNING"
    return ai_decision


def render_report(execution_report, pipeline_result, ollama_result, decision):
    """Render Markdown review output."""
    ai_text = ollama_result.get("response") or "Ollama is unavailable. Local rule-based review was used."
    summary = pipeline_result.get("summary", {})
    return f"""# n8n AI Review Report

## Created At

{utc_now()}

## Decision

{decision}

## n8n Execution

- Status: {execution_report.get("status")}
- Mode: {execution_report.get("mode")}
- Webhook configured: {execution_report.get("webhook_configured")}

## Test Pipeline

- Status: {summary.get("status")}
- Passed tests: {summary.get("passed_tests")}
- Failed tests: {summary.get("failed_tests")}
- Warnings: {summary.get("warnings")}

## Ollama

- URL: {DEFAULT_OLLAMA_URL}
- Model: {DEFAULT_MODEL}
- Available: {ollama_result.get("available")}
- Model available: {ollama_result.get("model_available")}
- Error: {ollama_result.get("error") or "None"}

## AI Advisory Review

{ai_text}

## Production Safety

- Production deployed: false
- Real secrets stored: false
- Human approval bypassed: false
- CI testing replaced: false

## Final Note

This report is advisory only. It does not authorize production deployment.
"""


def generate_review(execution_path=None, pipeline_path=None, output_path=None, ollama_url=DEFAULT_OLLAMA_URL, model=DEFAULT_MODEL):
    """Generate the n8n AI review report."""
    execution_report = load_json(execution_path or DEFAULT_EXECUTION_REPORT)
    pipeline_result = load_json(pipeline_path or DEFAULT_PIPELINE_RESULT)
    prompt = build_prompt(execution_report, pipeline_result)
    ollama_result = ask_ollama(prompt, model=model, ollama_url=ollama_url, timeout=60)
    decision = decide(execution_report, pipeline_result, ollama_result)
    report = render_report(execution_report, pipeline_result, ollama_result, decision)

    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    return {
        "phase": "13.3",
        "decision": decision,
        "ollama_available": ollama_result.get("available"),
        "model": model,
        "model_available": ollama_result.get("model_available"),
        "output": str(output),
        "auto_deploy": False,
        "auto_approve_production": False,
        "human_review_required": True,
    }


def main():
    """Command-line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Generate n8n Ollama advisory review.")
    parser.add_argument("--execution", default=None)
    parser.add_argument("--pipeline", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    result = generate_review(
        execution_path=args.execution,
        pipeline_path=args.pipeline,
        output_path=args.output,
        ollama_url=args.url,
        model=args.model,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
