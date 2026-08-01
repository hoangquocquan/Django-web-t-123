"""Run the complete AI Phase Review Engine flow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from evidence_collector import collect_evidence
from ollama_phase_reviewer import review_phase
from report_generator import generate_report
from requirement_validator import validate_requirements
from test_executor import execute_tests


def run_phase_review(phase="13.5", skip_migration=False):
    """Coordinate evidence, rules, tests, AI review, and report generation."""
    collect_evidence(phase=phase)
    rules = validate_requirements()
    tests = execute_tests(include_migration=not skip_migration)
    ai_review = review_phase()
    report = generate_report()
    if rules.get("status") != "PASS" or tests.get("status") != "PASS" or ai_review.get("status") == "BLOCKED":
        status = "BLOCKED"
    elif ai_review.get("status") == "WARNING":
        status = "WAITING_HUMAN_REVIEW"
    elif ai_review.get("status") == "PASS" and ai_review.get("gate_state") == "WAITING_HUMAN_APPROVAL":
        status = "WAITING_HUMAN_APPROVAL"
    else:
        status = "BLOCKED"

    result = {
        "phase": phase,
        "status": status,
        "evidence": "ai-review/evidence/current_phase.json",
        "rule_validation": "ai-review/results/rule_validation.json",
        "test_result": "ai-review/results/test_result.json",
        "ai_review": "ai-review/results/ai_review.json",
        "report": report.get("output"),
        "decision": report.get("decision"),
        "safety": {
            "production_approved": False,
            "code_modified_by_ai": False,
            "failed_tests_skipped": False,
            "human_approval_required": True,
        },
    }
    return result


def main():
    """Command-line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run AI Phase Review Engine.")
    parser.add_argument("--phase", default="13.5")
    parser.add_argument("--skip-migration", action="store_true")
    args = parser.parse_args()

    result = run_phase_review(phase=args.phase, skip_migration=args.skip_migration)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "WAITING_HUMAN_APPROVAL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
