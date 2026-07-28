"""Call local Ollama for AI phase review."""

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


DEFAULT_EVIDENCE = PROJECT_ROOT / "ai-review" / "evidence" / "current_phase.json"
DEFAULT_RULES = PROJECT_ROOT / "ai-review" / "results" / "rule_validation.json"
DEFAULT_TESTS = PROJECT_ROOT / "ai-review" / "results" / "test_result.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "ai-review" / "results" / "ai_review.json"
DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def utc_now():
    """Return an ISO timestamp for AI evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path):
    """Load JSON if available."""
    target = Path(path)
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def compact(value, limit=8000):
    """Compact JSON text for local prompt safety."""
    text = json.dumps(value, indent=2, ensure_ascii=False)
    return text[:limit]


def build_prompt(evidence, rule_validation, test_result):
    """Build the local Ollama review prompt."""
    return f"""
You are an AI Phase Review Engine for mecprecision-vietnam.

Rules:
- AI is reviewer only.
- Do not approve production deployment.
- Do not modify code automatically.
- Do not skip failed tests.
- Human approval remains required.

Evidence:
{compact(evidence)}

Rule validation:
{compact(rule_validation)}

Test result:
{compact(test_result)}

Return JSON-like content with:
status: PASS | WARNING | BLOCKED
summary:
issues:
recommendation:
production_safety:
""".strip()


def normalize_status(ai_text):
    """Normalize older PASS_WITH_WARNING wording to this engine's WARNING."""
    decision = parse_ai_decision(ai_text)
    if decision == "PASS_WITH_WARNING":
        return "WARNING"
    return "PASS" if decision == "PASS" else "BLOCKED"


def production_language_detected(ai_text):
    """Detect AI wording that sounds like production approval."""
    normalized = str(ai_text or "").lower()
    risky_phrases = [
        "ready for production",
        "approve production",
        "approved for production",
        "deploy to production",
        "production deployment approved",
    ]
    return any(phrase in normalized for phrase in risky_phrases)


def review_phase(
    evidence_path=DEFAULT_EVIDENCE,
    rule_path=DEFAULT_RULES,
    test_path=DEFAULT_TESTS,
    output_path=None,
    ollama_url=DEFAULT_OLLAMA_URL,
    model=DEFAULT_MODEL,
):
    """Run local Ollama review and write JSON output."""
    evidence = load_json(evidence_path)
    rule_validation = load_json(rule_path)
    test_result = load_json(test_path)

    if rule_validation.get("status") != "PASS" or test_result.get("status") != "PASS":
        ollama_result = {
            "available": False,
            "model_available": False,
            "response": "",
            "error": "Rule validation or tests failed; AI review blocked by deterministic checks.",
            "models": [],
        }
        status = "BLOCKED"
    else:
        prompt = build_prompt(evidence, rule_validation, test_result)
        ollama_result = ask_ollama(prompt, model=model, ollama_url=ollama_url, timeout=60)
        status = normalize_status(ollama_result.get("response")) if ollama_result.get("available") else "WARNING"
        if production_language_detected(ollama_result.get("response")) and status == "PASS":
            status = "WARNING"

    result = {
        "phase": evidence.get("phase", "unknown"),
        "created_at": utc_now(),
        "status": status,
        "summary": "AI review completed." if ollama_result.get("available") else "AI review used safe fallback.",
        "issues": (
            []
            if status == "PASS"
            else ["Review requires human attention."]
            + (
                ["AI response contained production-approval-like wording."]
                if production_language_detected(ollama_result.get("response"))
                else []
            )
        ),
        "recommendation": "Proceed to human review; do not auto approve production.",
        "ollama": {
            "url": ollama_url,
            "model": model,
            "available": ollama_result.get("available"),
            "model_available": ollama_result.get("model_available"),
            "installed_models": ollama_result.get("models", []),
            "error": ollama_result.get("error") or "",
            "response": ollama_result.get("response") or "",
        },
        "safety": {
            "production_approved": False,
            "code_modified_by_ai": False,
            "failed_tests_skipped": False,
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

    parser = argparse.ArgumentParser(description="Run Ollama phase review.")
    parser.add_argument("--evidence", default=str(DEFAULT_EVIDENCE))
    parser.add_argument("--rules", default=str(DEFAULT_RULES))
    parser.add_argument("--tests", default=str(DEFAULT_TESTS))
    parser.add_argument("--output", default=None)
    parser.add_argument("--url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    result = review_phase(
        evidence_path=args.evidence,
        rule_path=args.rules,
        test_path=args.tests,
        output_path=args.output,
        ollama_url=args.url,
        model=args.model,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
