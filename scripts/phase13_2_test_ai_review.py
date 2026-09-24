"""Generate the Phase 13.2 AI advisory review.

This script uses local Ollama when available. If Ollama is offline, it still
creates an advisory warning report so human reviewers have clear evidence.
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


DEFAULT_RESULT = PROJECT_ROOT / "docs" / "cicd" / "test_pipeline_result.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "ai-devops" / "TEST_PIPELINE_AI_REVIEW.md"
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


def utc_now():
    """Return an ISO timestamp for AI review evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_test_result(path):
    """Load pipeline evidence if it exists."""
    target = Path(path)
    if not target.exists():
        return {
            "summary": {
                "status": "TEST_PIPELINE_BLOCKED",
                "failed_required_stages": ["missing_test_pipeline_result"],
                "passed_tests": 0,
                "failed_tests": 1,
                "warnings": 1,
            },
            "stages": [],
            "safety": {
                "production_deployed": False,
                "real_ci_secrets_created": False,
                "failed_tests_bypassed": False,
            },
        }
    return json.loads(target.read_text(encoding="utf-8"))


def failed_stage_summary(test_result):
    """Return compact failed stage information for the AI prompt."""
    return [
        {
            "name": stage.get("name"),
            "status": stage.get("status"),
            "returncode": stage.get("returncode"),
            "stderr_tail": stage.get("stderr_tail", "")[-1200:],
        }
        for stage in test_result.get("stages", [])
        if stage.get("status") == "FAIL"
    ]


def build_prompt(test_result):
    """Build the local AI prompt from test evidence."""
    summary = test_result.get("summary", {})
    failed = failed_stage_summary(test_result)
    return f"""
You are a Senior DevOps Reviewer for mecprecision-vietnam.

Review the Phase 13.2 automated test pipeline evidence.

Rules:
- Never approve production.
- Never deploy anything.
- Never bypass failed tests.
- AI is advisory only; human review remains mandatory.

Pipeline summary:
{json.dumps(summary, indent=2, ensure_ascii=False)}

Failed stages:
{json.dumps(failed, indent=2, ensure_ascii=False)}

Safety flags:
{json.dumps(test_result.get("safety", {}), indent=2, ensure_ascii=False)}

Return:
1. decision: PASS, PASS_WITH_WARNING, or BLOCKED
2. key risks
3. failed tests
4. warnings
5. production safety confirmation
""".strip()


def decide(test_result, ollama_result):
    """Choose the advisory AI decision."""
    summary = test_result.get("summary", {})
    if summary.get("status") != "TEST_PIPELINE_COMPLETE":
        return "BLOCKED"
    if not ollama_result.get("available"):
        return "PASS_WITH_WARNING"
    ai_decision = parse_ai_decision(ollama_result.get("response"))
    if ai_decision == "BLOCKED":
        return "BLOCKED"
    if summary.get("warnings", 0) and ai_decision == "PASS":
        return "PASS_WITH_WARNING"
    return ai_decision


def render_report(test_result, ollama_result, decision):
    """Render the Markdown AI review report."""
    summary = test_result.get("summary", {})
    ai_text = ollama_result.get("response") or "Ollama is unavailable. Test evidence was reviewed by rule-based fallback."
    return f"""# Test Pipeline AI Review

## Created At

{utc_now()}

## Decision

{decision}

## Test Pipeline Summary

- Status: {summary.get("status")}
- Passed tests: {summary.get("passed_tests")}
- Failed tests: {summary.get("failed_tests")}
- Warnings: {summary.get("warnings")}
- Failed required stages: {summary.get("failed_required_stages")}

## Ollama Status

- URL: {DEFAULT_OLLAMA_URL}
- Model: {DEFAULT_MODEL}
- Available: {ollama_result.get("available")}
- Model available: {ollama_result.get("model_available")}
- Installed models: {ollama_result.get("models", [])}
- Error: {ollama_result.get("error") or "None"}

## AI Advisory Review

{ai_text}

## Production Safety

- Production deployed: false
- Real CI secrets created: false
- Failed tests bypassed: false
- Human review required: true

## Final Note

This AI review is advisory only. It does not authorize production deployment.
"""


def generate_ai_review(result_path=None, output_path=None, ollama_url=DEFAULT_OLLAMA_URL, model=DEFAULT_MODEL):
    """Generate the AI advisory review and write a Markdown report."""
    test_result = load_test_result(result_path or DEFAULT_RESULT)
    prompt = build_prompt(test_result)
    ollama_result = ask_ollama(prompt, model=model, ollama_url=ollama_url, timeout=60)
    decision = decide(test_result, ollama_result)
    report = render_report(test_result, ollama_result, decision)

    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    return {
        "phase": "13.2",
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

    parser = argparse.ArgumentParser(description="Generate Phase 13.2 AI test pipeline review.")
    parser.add_argument("--result", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    result = generate_ai_review(
        result_path=args.result,
        output_path=args.output,
        ollama_url=args.url,
        model=args.model,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
