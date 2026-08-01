import importlib.util
import json
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = PROJECT_ROOT / "ai-review"
if str(REVIEW_DIR) not in sys.path:
    sys.path.insert(0, str(REVIEW_DIR))

from mandatory_review import (
    PROMPT_VERSION,
    REQUIRED_FIELDS,
    REVIEW_JSON_SCHEMA,
    TransportResult,
    build_review_prompt,
    review_json_schema,
    run_mandatory_review,
)
from scripts import n8n_phase_trigger


def load_evidence_collector():
    spec = importlib.util.spec_from_file_location("ai05_evidence_collector", REVIEW_DIR / "evidence_collector.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def review_evidence():
    return {
        "phase": "AI-05",
        "correlation_id": "review-correlation",
        "phase_specification": {"path": "spec.md", "content": "Mandatory local review specification."},
        "git": {"base_commit": "a" * 40, "current_commit": "b" * 40},
        "actual_git_diff": {
            "sha256": "c" * 64,
            "changed_files": ["M\tai-review/mandatory_review.py"],
            "stat": "1 file changed",
            "patch_preview": "+fail closed",
        },
        "migrations": [],
        "test_result_hashes": {"tests.json": "d" * 64},
    }


def valid_review(decision="PASS", critical=None, high=None):
    return {
        "decision": decision,
        "summary": "Actual diff and tests were reviewed. Production is not approved.",
        "requirements_checked": ["fail closed", "actual diff"],
        "missing_requirements": [],
        "critical_findings": critical or [],
        "high_findings": high or [],
        "medium_findings": [],
        "security_findings": [],
        "test_findings": [],
        "migration_findings": [],
        "recommended_actions": ["Continue to human architecture review."],
        "requires_human_review": True,
        "model": "llama3",
        "prompt_version": PROMPT_VERSION,
    }


class FakeTransport:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def generate(self, prompt, model, url, timeout):
        self.calls.append({"prompt": prompt, "model": model, "url": url, "timeout": timeout})
        return self.outcomes.pop(0)


def run_gate(transport, evidence=None, retries=3, required=True):
    return run_mandatory_review(
        evidence=evidence or review_evidence(),
        rules={"status": "PASS"},
        tests={"status": "PASS"},
        transport=transport,
        required=required,
        model="llama3",
        max_retries=retries,
    )


@pytest.mark.parametrize("error_type", ["unavailable", "model_missing", "timeout"])
def test_required_review_blocks_runtime_failures(error_type):
    transport = FakeTransport([TransportResult(False, error="runtime failure", error_type=error_type)] * 3)

    result = run_gate(transport)

    assert result["status"] == "BLOCKED"
    assert result["gate_state"] == "BLOCKED"
    assert result["review_completed"] is False
    assert result["fallback_used"] is False


def test_invalid_json_and_schema_mismatch_are_blocked_after_three_attempts():
    invalid_schema = valid_review()
    invalid_schema.pop("requires_human_review")
    transport = FakeTransport([
        TransportResult(True, response="not-json"),
        TransportResult(True, response=json.dumps(invalid_schema)),
        TransportResult(True, response="[]"),
    ])

    result = run_gate(transport, retries=99)

    assert result["status"] == "BLOCKED"
    assert result["attempts"] == 3
    assert len(transport.calls) == 3
    assert result["schema_valid"] is False


def test_ollama_structured_output_schema_is_strict():
    assert set(REVIEW_JSON_SCHEMA["required"]) == REQUIRED_FIELDS
    assert REVIEW_JSON_SCHEMA["additionalProperties"] is False
    assert REVIEW_JSON_SCHEMA["properties"]["requires_human_review"]["const"] is True
    assert REVIEW_JSON_SCHEMA["properties"]["prompt_version"]["const"] == PROMPT_VERSION
    assert review_json_schema("local-model")["properties"]["model"]["const"] == "local-model"


def test_evidence_collector_uses_commit_range_after_task_commit():
    collector = load_evidence_collector()
    assert collector.git_diff_args("base-sha", "current-sha") == ["base-sha", "HEAD"]
    assert collector.git_diff_args("same-sha", "same-sha") == ["HEAD"]


def test_prompt_or_source_leakage_in_summary_is_blocked():
    payload = valid_review()
    payload["summary"] = "Review summary copied from json.dumps(evidence_summary), which is not acceptable."
    result = run_gate(FakeTransport([TransportResult(True, response=json.dumps(payload))]), retries=1)
    assert result["status"] == "BLOCKED"
    assert "leakage" in result["issues"][0]


def test_missing_requirement_overrides_model_pass():
    payload = valid_review()
    payload["missing_requirements"] = ["Security evidence is missing."]
    result = run_gate(FakeTransport([TransportResult(True, response=json.dumps(payload))]), retries=1)
    assert result["status"] == "BLOCKED"
    assert result["gate_state"] == "BLOCKED"


def test_schema_retry_includes_specific_correction_feedback():
    leaked = valid_review()
    leaked["summary"] = "Copied json.dumps(evidence_summary) source instead of a review summary."
    transport = FakeTransport([
        TransportResult(True, response=json.dumps(leaked)),
        TransportResult(True, response=json.dumps(valid_review())),
    ])

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert result["attempts"] == 2
    assert "CORRECTION FEEDBACK" in transport.calls[1]["prompt"]
    assert "source-code leakage" in transport.calls[1]["prompt"]


def test_prompt_distinguishes_safety_prohibitions_from_production_approval():
    evidence = review_evidence()
    evidence["generated_reports"] = [{"status": "FAILED", "stale": True}]
    prompt = build_review_prompt(evidence, {"status": "PASS"}, {"status": "PASS"}, "llama3")
    assert "required safety controls" in prompt
    assert "affirmative bypasses" in prompt
    assert "generated_reports" not in prompt
    assert '"patch_preview": "+fail closed"' in prompt
    assert '"review_mode": "PRE_COMMIT_STAGED_DIFF"' in prompt
    assert '"diff_evidence_complete": true' in prompt
    assert "+fail closed" not in prompt.system
    assert "actual_git_diff" in prompt.user
    assert prompt.output_schema["properties"]["test_findings"]["maxItems"] == 0
    assert prompt.output_schema["properties"]["migration_findings"]["maxItems"] == 0


def test_review_evidence_json_is_complete_when_raw_patch_is_large():
    evidence = review_evidence()
    evidence["actual_git_diff"]["patch_preview"] = "+safe code\n" * 5000
    prompt = build_review_prompt(evidence, {"status": "PASS"}, {"status": "PASS"}, "llama3")
    evidence_text = prompt.user.split("Evidence: ", 1)[1]
    projected = json.loads(evidence_text)
    assert projected["actual_git_diff"]["review_projection_truncated"] is True
    assert len(projected["actual_git_diff"]["patch_preview"]) == 12000


def test_pass_cannot_recommend_deployment_and_gets_correction_retry():
    unsafe = valid_review()
    unsafe["summary"] = "The change is safe for deployment after the automated review."
    unsafe["recommended_actions"] = ["Deploy the code changes."]
    transport = FakeTransport([
        TransportResult(True, response=json.dumps(unsafe)),
        TransportResult(True, response=json.dumps(valid_review())),
    ])

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert result["attempts"] == 2
    assert "attempted to authorize deployment" in transport.calls[1]["prompt"]


def test_last_attempt_with_deployment_authorization_is_blocked():
    unsafe = valid_review()
    unsafe["recommended_actions"] = ["Proceed with deployment."]
    result = run_gate(
        FakeTransport([TransportResult(True, response=json.dumps(unsafe))]),
        retries=1,
    )
    assert result["status"] == "BLOCKED"
    assert "authorization language" in result["review"]["security_findings"][-1]


def test_hallucinated_missing_diff_is_retried_against_verified_evidence():
    contradictory = valid_review(decision="BLOCKED", critical=["Actual Git diff evidence is incomplete."])
    contradictory["missing_requirements"] = ["actual_git_evidence_required"]
    transport = FakeTransport([
        TransportResult(True, response=json.dumps(contradictory)),
        TransportResult(True, response=json.dumps(valid_review())),
    ])

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert result["attempts"] == 2
    assert "contradicts verified complete Git diff evidence" in transport.calls[1]["prompt"]


def test_correction_loop_metadata_cannot_be_reported_as_product_finding():
    self_referential = valid_review(decision="BLOCKED", critical=["Review summary contains prompt leakage."])
    self_referential["summary"] = "The previous response requires the operator to re-run the AI model."
    transport = FakeTransport([
        TransportResult(True, response=json.dumps(self_referential)),
        TransportResult(True, response=json.dumps(valid_review())),
    ])

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert "correction-loop metadata" in transport.calls[1]["prompt"]


def test_pass_with_placeholder_high_findings_is_retried():
    placeholder = valid_review(high=["High finding 1"])
    transport = FakeTransport([
        TransportResult(True, response=json.dumps(placeholder)),
        TransportResult(True, response=json.dumps(valid_review())),
    ])

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert "generic placeholder findings" in transport.calls[1]["prompt"]


def test_missing_human_approval_is_not_a_technical_blocker():
    human_gate = valid_review(decision="BLOCKED")
    human_gate["summary"] = "The code modification is not approved by a human reviewer."
    human_gate["medium_findings"] = ["Get approval from a human reviewer."]
    transport = FakeTransport([
        TransportResult(True, response=json.dumps(human_gate)),
        TransportResult(True, response=json.dumps(valid_review())),
    ])

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert "expected later human gate" in transport.calls[1]["prompt"]


@pytest.mark.parametrize(
    "decision,expected_gate",
    [
        ("PASS", "WAITING_HUMAN_APPROVAL"),
        ("WARNING", "WAITING_HUMAN_REVIEW"),
        ("BLOCKED", "BLOCKED"),
    ],
)
def test_review_decisions_map_to_explicit_gate_states(decision, expected_gate):
    transport = FakeTransport([TransportResult(True, response=json.dumps(valid_review(decision)))])

    result = run_gate(transport)

    assert result["status"] == decision
    assert result["gate_state"] == expected_gate
    assert result["review_completed"] is True
    assert result["fallback_used"] is False


@pytest.mark.parametrize("field", ["critical_findings", "high_findings"])
def test_critical_or_high_finding_overrides_model_pass(field):
    payload = valid_review()
    payload[field] = ["Unsafe bypass detected."]

    result = run_gate(FakeTransport([TransportResult(True, response=json.dumps(payload))]))

    assert result["status"] == "BLOCKED"
    assert result["gate_state"] == "BLOCKED"


def test_ai_cannot_waive_human_review():
    payload = valid_review()
    payload["requires_human_review"] = False

    result = run_gate(FakeTransport([TransportResult(True, response=json.dumps(payload))]), retries=1)

    assert result["status"] == "BLOCKED"
    assert "AI cannot waive human review" in result["issues"][0]


def test_optional_mode_or_fallback_never_turns_offline_review_into_pass():
    result = run_gate(
        FakeTransport([TransportResult(False, error="offline", error_type="unavailable")]),
        retries=1,
        required=False,
    )

    assert result["status"] == "BLOCKED"
    assert result["fallback_used"] is False


def test_actual_git_diff_is_mandatory_and_is_sent_to_reviewer():
    incomplete = review_evidence()
    incomplete["actual_git_diff"] = {}
    transport = FakeTransport([TransportResult(True, response=json.dumps(valid_review()))])

    blocked = run_gate(transport, evidence=incomplete)

    assert blocked["status"] == "BLOCKED"
    assert transport.calls == []

    valid_transport = FakeTransport([TransportResult(True, response=json.dumps(valid_review()))])
    passed = run_gate(valid_transport)
    assert passed["status"] == "PASS"
    assert "fail closed" in valid_transport.calls[0]["prompt"]
    assert "cccccccc" in valid_transport.calls[0]["prompt"]


def test_n8n_does_not_advance_from_successful_process_without_pass_gate(monkeypatch):
    calls = []

    def fake_run_command(args, timeout=900):
        calls.append(args)
        if "phase_validator.py" in args:
            return {"returncode": 0, "stdout_tail": json.dumps({"status": "PASS"}), "status": "PASS"}
        if any(str(arg).endswith("run_phase_review.py") for arg in args):
            return {
                "returncode": 0,
                "stdout_tail": json.dumps({"status": "BLOCKED", "decision": "PASS"}),
                "status": "PASS",
            }
        return {"returncode": 0, "stdout_tail": json.dumps({"status": "BLOCKED"}), "status": "PASS"}

    monkeypatch.setattr(n8n_phase_trigger, "run_command", fake_run_command)

    result = n8n_phase_trigger.run_local_controller("AI-05")

    assert result["status"] == "CORRECTION_REQUIRED"
    assert result["status"] != "WAITING_HUMAN_APPROVAL"


def test_ai_factory_does_not_advance_from_exit_code_alone(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("mandatory_factory_runner", PROJECT_ROOT / "ai-factory" / "run_ai_factory.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    def fake_run_command(args, timeout=900):
        if any(str(arg).endswith("run_phase_review.py") for arg in args):
            stdout = json.dumps({"status": "BLOCKED", "decision": "PASS"})
        else:
            stdout = json.dumps({"status": "PASS"})
        return {"command": "test", "returncode": 0, "duration_seconds": 0, "stdout_tail": stdout, "stderr_tail": "", "status": "PASS"}

    monkeypatch.setattr(runner, "run_command", fake_run_command)
    monkeypatch.setattr(runner, "build_evidence_package", lambda **kwargs: {"phase": "AI-05"})
    monkeypatch.setattr(runner, "generate_final_report", lambda: {"decision": "BLOCKED"})
    monkeypatch.setattr(runner, "DEFAULT_RESULT", tmp_path / "factory.json")

    result = runner.run_factory("AI-05")

    assert result["status"] == "AI_SOFTWARE_FACTORY_BLOCKED"
    assert result["review_gate_passed"] is False
