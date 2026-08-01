"""Generate final Markdown report for AI phase review."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = PROJECT_ROOT / "ai-review" / "evidence" / "current_phase.json"
DEFAULT_RULES = PROJECT_ROOT / "ai-review" / "results" / "rule_validation.json"
DEFAULT_TESTS = PROJECT_ROOT / "ai-review" / "results" / "test_result.json"
DEFAULT_AI = PROJECT_ROOT / "ai-review" / "results" / "ai_review.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "reviews" / "PHASE_AI_REVIEW_REPORT.md"


def utc_now():
    """Return an ISO timestamp for report evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path):
    """Load JSON if available."""
    target = Path(path)
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def final_decision(rule_validation, test_result, ai_review):
    """Calculate final engine decision without auto-approving production."""
    if rule_validation.get("status") != "PASS":
        return "BLOCKED"
    if test_result.get("status") != "PASS":
        return "BLOCKED"
    if ai_review.get("status") == "BLOCKED":
        return "BLOCKED"
    if not ai_review.get("review_completed") or ai_review.get("fallback_used"):
        return "BLOCKED"
    if ai_review.get("status") == "WARNING":
        return "WARNING"
    if ai_review.get("status") == "PASS" and ai_review.get("gate_state") == "WAITING_HUMAN_APPROVAL":
        return "PASS"
    return "BLOCKED"


def render_report(evidence, rule_validation, test_result, ai_review):
    """Render the final Markdown report."""
    decision = final_decision(rule_validation, test_result, ai_review)
    return f"""# AI Phase Review Report

## Phase Name

{evidence.get("phase", "unknown")}

## Created At

{utc_now()}

## Final Decision

{decision}

## Requirement Status

- Status: {rule_validation.get("status")}
- Missing: {rule_validation.get("missing", [])}
- Warnings: {rule_validation.get("warnings", [])}
- Forbidden changes: {rule_validation.get("forbidden_changes", [])}

## Test Status

- Status: {test_result.get("status")}
- Failed required checks: {test_result.get("failed_required", [])}
- Duration seconds: {test_result.get("duration_seconds")}

## Security Status

- Production approved by AI: false
- Code modified automatically by AI: false
- Failed tests skipped: false
- Human approval required: true

## AI Analysis

- Status: {ai_review.get("status")}
- Summary: {ai_review.get("summary")}
- Issues: {ai_review.get("issues", [])}
- Recommendation: {ai_review.get("recommendation")}
- Ollama available: {(ai_review.get("ollama") or {}).get("available")}
- Ollama model: {(ai_review.get("ollama") or {}).get("model")}
- Review completed: {ai_review.get("review_completed")}
- Schema valid: {ai_review.get("schema_valid")}
- Fallback used: {ai_review.get("fallback_used")}
- Gate state: {ai_review.get("gate_state")}

## Production Safety

This report does not authorize production deployment. Human architecture review
and explicit approval remain required.
"""


def generate_report(
    evidence_path=DEFAULT_EVIDENCE,
    rule_path=DEFAULT_RULES,
    test_path=DEFAULT_TESTS,
    ai_path=DEFAULT_AI,
    output_path=None,
):
    """Generate final Markdown report and return summary."""
    evidence = load_json(evidence_path)
    rule_validation = load_json(rule_path)
    test_result = load_json(test_path)
    ai_review = load_json(ai_path)
    report = render_report(evidence, rule_validation, test_result, ai_review)

    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    return {
        "phase": evidence.get("phase", "unknown"),
        "decision": final_decision(rule_validation, test_result, ai_review),
        "output": str(output),
        "production_approved": False,
        "human_approval_required": True,
    }


def main():
    """Command-line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Generate final AI phase review report.")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    result = generate_report(output_path=args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
