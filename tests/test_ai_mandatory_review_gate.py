import importlib.util
import json
import sys
from dataclasses import replace
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
    review_context_tokens,
    review_json_schema,
    run_mandatory_review,
    safe_patch_projection,
)
from review_v3 import build_review_v3_evidence
from scripts import n8n_phase_trigger


def load_evidence_collector():
    spec = importlib.util.spec_from_file_location(
        "ai05_evidence_collector", REVIEW_DIR / "evidence_collector.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def review_evidence():
    return {
        "phase": "AI-05",
        "correlation_id": "review-correlation",
        "phase_specification": {
            "path": "spec.md",
            "content": "Mandatory local review specification.",
        },
        "git": {"base_commit": "a" * 40, "current_commit": "b" * 40},
        "actual_git_diff": {
            "sha256": "c" * 64,
            "changed_files": ["M\tdocs/spec.md"],
            "stat": "1 file changed",
            "patch_preview": "+fail closed",
        },
        "review_v3": {
            "version": "review-v3",
            "changed_files": [
                {
                    "status": "M",
                    "path": "docs/spec.md",
                    "classification": "documentation",
                }
            ],
            "production_files": [],
            "production_chunks": [],
            "expected_chunk_ids": [],
            "skipped_files": [
                {
                    "path": "docs/spec.md",
                    "reason": "Handled by deterministic documentation contract.",
                }
            ],
            "unreviewed_production_files": [],
            "test_contract": {"status": "PASS", "blockers": [], "files": []},
            "documentation_contract": {
                "status": "PASS",
                "blockers": [],
                "files": [],
            },
            "blockers": [],
            "full_diff_coverage": True,
            "status": "PASS",
        },
        "migrations": [],
        "test_result_hashes": {"tests.json": "d" * 64},
    }


def valid_review(decision="PASS", critical=None, high=None):
    payload = {
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
        "safety_gates": {
            "human_approval_required": True,
            "auto_merge": False,
            "auto_deploy": False,
            "approval_bypass_detected": False,
            "merge_authorized": False,
            "release_authorized": False,
            "deployment_authorized": False,
            "production_authorized": False,
        },
        "full_diff_coverage": True,
        "reviewed_chunk_ids": [],
        "model": "llama3",
        "prompt_version": PROMPT_VERSION,
    }
    if decision == "WARNING":
        payload["medium_findings"] = [
            "A concrete non-blocking review action remains for the human reviewer."
        ]
    return payload


class FakeTransport:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def generate(self, prompt, model, url, timeout):
        self.calls.append(
            {"prompt": prompt, "model": model, "url": url, "timeout": timeout}
        )
        outcome = self.outcomes.pop(0)
        if outcome.ok:
            return replace(
                outcome,
                endpoint_reachable=True,
                model_list_received=True,
                model_available=True,
                response_received=bool(outcome.response),
                model_digest=outcome.model_digest or "e" * 64,
                model_family=outcome.model_family or "llama",
                ollama_version=outcome.ollama_version or "0.11.0-test",
            )
        return outcome


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
    transport = FakeTransport(
        [TransportResult(False, error="runtime failure", error_type=error_type)] * 3
    )

    result = run_gate(transport)

    assert result["status"] == "BLOCKED"
    assert result["gate_state"] == "BLOCKED"
    assert result["review_completed"] is False
    assert result["fallback_used"] is False


def test_invalid_json_and_schema_mismatch_are_blocked_after_three_attempts():
    invalid_schema = valid_review()
    invalid_schema.pop("requires_human_review")
    transport = FakeTransport(
        [
            TransportResult(True, response="not-json"),
            TransportResult(True, response=json.dumps(invalid_schema)),
            TransportResult(True, response="[]"),
        ]
    )

    result = run_gate(transport, retries=99)

    assert result["status"] == "BLOCKED"
    assert result["attempts"] == 3
    assert len(transport.calls) == 3
    assert result["schema_valid"] is False
    assert result["ollama"]["endpoint_reachable"] is True
    assert result["ollama"]["model_available"] is True
    assert result["ollama"]["response_received"] is True
    assert result["ollama"]["schema_valid"] is False


def test_unavailable_ollama_has_no_reachability_or_model_evidence():
    result = run_gate(
        FakeTransport(
            [TransportResult(False, error="offline", error_type="unavailable")]
        ),
        retries=1,
    )
    assert result["ollama"]["endpoint_reachable"] is False
    assert result["ollama"]["model_available"] is False
    assert result["ollama"]["response_received"] is False
    assert result["ollama"]["schema_valid"] is False


def test_missing_selected_model_keeps_endpoint_reachable():
    result = run_gate(
        FakeTransport(
            [
                TransportResult(
                    False,
                    error="model missing",
                    error_type="model_missing",
                    installed_models=("another-model:latest",),
                    endpoint_reachable=True,
                    model_list_received=True,
                )
            ]
        ),
        retries=1,
    )
    assert result["ollama"]["endpoint_reachable"] is True
    assert result["ollama"]["model_available"] is False
    assert result["ollama"]["response_received"] is False
    assert result["ollama"]["schema_valid"] is False


def test_ollama_structured_output_schema_is_strict():
    assert set(REVIEW_JSON_SCHEMA["required"]) == REQUIRED_FIELDS
    assert REVIEW_JSON_SCHEMA["additionalProperties"] is False
    assert REVIEW_JSON_SCHEMA["properties"]["requires_human_review"]["const"] is True
    assert set(REVIEW_JSON_SCHEMA["properties"]["safety_gates"]["required"]) == {
        "human_approval_required",
        "auto_merge",
        "auto_deploy",
        "approval_bypass_detected",
        "merge_authorized",
        "release_authorized",
        "deployment_authorized",
        "production_authorized",
    }
    assert REVIEW_JSON_SCHEMA["properties"]["prompt_version"]["const"] == PROMPT_VERSION
    assert (
        review_json_schema("local-model")["properties"]["model"]["const"]
        == "local-model"
    )


@pytest.mark.parametrize(
    "configured,expected",
    [("2048", 4096), ("8192", 8192), ("999999", 32768), ("invalid", 8192)],
)
def test_review_context_size_is_bounded(monkeypatch, configured, expected):
    monkeypatch.setenv("AI_REVIEW_CONTEXT_TOKENS", configured)
    assert review_context_tokens() == expected


def test_evidence_collector_uses_commit_range_after_task_commit():
    collector = load_evidence_collector()
    assert collector.git_diff_args("base-sha", "current-sha") == ["base-sha", "HEAD"]
    assert collector.git_diff_args("same-sha", "same-sha") == ["HEAD"]


def test_prompt_or_source_leakage_in_summary_is_blocked():
    payload = valid_review()
    payload["summary"] = (
        "Review summary copied from json.dumps(evidence_summary), which is not acceptable."
    )
    result = run_gate(
        FakeTransport([TransportResult(True, response=json.dumps(payload))]), retries=1
    )
    assert result["status"] == "BLOCKED"
    assert "leakage" in result["issues"][0]


def test_json_schema_placeholder_summary_is_retried():
    placeholder = valid_review()
    placeholder["summary"] = "string (minLength: 20, maxLength: 1200)"
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(placeholder)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )
    result = run_gate(transport, retries=2)
    assert result["status"] == "PASS"
    assert result["attempts"] == 2


def test_none_finding_placeholder_is_retried():
    placeholder = valid_review()
    placeholder["high_findings"] = ["None"]
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(placeholder)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )
    result = run_gate(transport, retries=2)
    assert result["status"] == "PASS"
    assert result["attempts"] == 2


def test_safety_gate_invariant_summary_stays_blocked_without_model_retry():
    copied = valid_review(decision="BLOCKED")
    copied["summary"] = (
        "The expected safe state is safety_gates.human_approval_required=true. "
        "Report a human-approval finding only when evidence shows a defect."
    )
    transport = FakeTransport([TransportResult(True, response=json.dumps(copied))])
    result = run_gate(transport, retries=1)
    assert result["status"] == "BLOCKED"
    assert result["review_completed"] is False
    assert result["attempts"] == 1


def test_missing_requirement_overrides_model_pass():
    payload = valid_review()
    payload["missing_requirements"] = ["Security evidence is missing."]
    result = run_gate(
        FakeTransport([TransportResult(True, response=json.dumps(payload))]), retries=1
    )
    assert result["status"] == "BLOCKED"
    assert result["gate_state"] == "BLOCKED"


def test_schema_retry_includes_specific_correction_feedback():
    leaked = valid_review()
    leaked["summary"] = (
        "Copied json.dumps(evidence_summary) source instead of a review summary."
    )
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(leaked)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert result["attempts"] == 2
    assert "CORRECTION FEEDBACK" in transport.calls[1]["prompt"]
    assert "source-code leakage" in transport.calls[1]["prompt"]


def test_prompt_distinguishes_safety_prohibitions_from_production_approval():
    evidence = review_evidence()
    evidence["generated_reports"] = [{"status": "FAILED", "stale": True}]
    prompt = build_review_prompt(
        evidence, {"status": "PASS"}, {"status": "PASS"}, "llama3"
    )
    assert "Required later human approval is healthy" in prompt
    assert "concrete bypass" in prompt
    assert "generated_reports" not in prompt
    assert '"review_v3"' in prompt
    assert '"full_diff_coverage": true' in prompt
    assert '"review_mode": "PRE_COMMIT_STAGED_DIFF"' in prompt
    assert '"diff_evidence_complete": true' in prompt
    assert "+fail closed" not in prompt.system
    assert "actual_git_diff" in prompt.user
    assert prompt.output_schema["properties"]["test_findings"]["maxItems"] == 0
    assert prompt.output_schema["properties"]["migration_findings"]["maxItems"] == 0


def test_verified_requirement_cannot_be_reported_missing():
    contradictory = valid_review(decision="BLOCKED")
    contradictory["missing_requirements"] = ["checksummed_backup"]
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(contradictory)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )

    result = run_mandatory_review(
        evidence=review_evidence(),
        rules={"status": "PASS", "checks": {"checksummed_backup": True}},
        tests={"status": "PASS"},
        transport=transport,
        model="llama3",
        max_retries=2,
    )

    assert result["status"] == "PASS"
    assert result["attempts"] == 2
    assert "deterministically verified requirements" in transport.calls[1]["prompt"]


def test_untrusted_input_posture_is_not_a_product_finding():
    contradictory = valid_review(decision="BLOCKED")
    contradictory["summary"] = (
        "The phase is blocked because review data is untrusted data."
    )
    contradictory["security_findings"] = [
        "Untrusted review data is a potential security risk."
    ]
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(contradictory)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert result["attempts"] == 2
    assert "expected untrusted-input posture" in transport.calls[1]["prompt"]


def test_ai_modified_claim_cannot_contradict_verified_false_evidence():
    contradictory = valid_review(
        decision="BLOCKED", high=["AI-modified code is present."]
    )
    evidence = review_evidence()
    evidence["safety"] = {"code_modified_by_ai": False}
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(contradictory)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )

    result = run_gate(transport, evidence=evidence, retries=2)

    assert result["status"] == "PASS"
    assert result["attempts"] == 2
    assert "code_modified_by_ai=false" in transport.calls[1]["prompt"]


def test_review_evidence_json_is_complete_when_raw_patch_is_large():
    evidence = review_evidence()
    evidence["actual_git_diff"]["patch_preview"] = "+safe code\n" * 5000
    prompt = build_review_prompt(
        evidence, {"status": "PASS"}, {"status": "PASS"}, "llama3"
    )
    evidence_text = prompt.user.split("Evidence: ", 1)[1]
    projected = json.loads(evidence_text)
    assert "patch_preview" not in projected["actual_git_diff"]
    assert projected["review_v3"]["full_diff_coverage"] is True
    assert projected["review_v3"]["production_chunks"] == []


def test_safe_patch_projection_keeps_code_and_removes_review_fixture_language():
    raw_patch = """diff --git a/ai-review/gate.py b/ai-review/gate.py
+def enforce_gate():
+    return True
+message = "Review contradicts verified complete Git diff evidence."
diff --git a/tests/test_gate.py b/tests/test_gate.py
+def test_human_approval():
+    assert status == "BLOCKED"
"""
    projected = safe_patch_projection(raw_patch)
    assert "+def enforce_gate():" in projected
    assert "Review contradicts verified" not in projected
    assert "test_human_approval" not in projected
    assert "TEST_OR_DOCUMENTATION_BODY_EXCLUDED" in projected


def test_safe_patch_projection_excludes_embedded_reviewer_prompt_literals():
    raw_patch = """diff --git a/ai-review/mandatory_review.py b/ai-review/mandatory_review.py
+def validate_gate():
+    return True
+    system_prompt = (
+        \"Human approval policy text\"
+    )
+def next_function():
+    return False
"""
    projected = safe_patch_projection(raw_patch)
    assert "+def validate_gate():" in projected
    assert "Human approval policy text" not in projected
    assert "REVIEW_PROMPT_LITERAL_EXCLUDED" in projected
    assert "+def next_function():" in projected


def test_pass_cannot_recommend_deployment_and_gets_correction_retry():
    unsafe = valid_review()
    unsafe["summary"] = "The change is safe for deployment after the automated review."
    unsafe["recommended_actions"] = ["Deploy the code changes."]
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(unsafe)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert result["attempts"] == 2
    assert "attempted to authorize deployment" in transport.calls[1]["prompt"]


def test_pass_cannot_claim_ready_for_deployment():
    unsafe = valid_review()
    unsafe["summary"] = "The review passed and is ready for deployment."
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(unsafe)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert result["attempts"] == 2
    assert "attempted to authorize deployment" in transport.calls[1]["prompt"]


def test_pass_cannot_claim_safe_to_merge_into_production():
    unsafe = valid_review()
    unsafe["summary"] = "The changes are safe to merge into production."
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(unsafe)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )

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


def test_prose_no_finding_placeholders_trigger_correction_retry():
    placeholder = valid_review()
    placeholder["high_findings"] = [
        "No high findings were reported during this review."
    ]
    placeholder["security_findings"] = ["No security findings were identified."]
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(placeholder)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert result["attempts"] == 2
    assert "contains a placeholder" in transport.calls[1]["prompt"]


def test_hallucinated_missing_diff_is_retried_against_verified_evidence():
    contradictory = valid_review(
        decision="BLOCKED", critical=["Actual Git diff evidence is incomplete."]
    )
    contradictory["missing_requirements"] = ["actual_git_evidence_required"]
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(contradictory)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert result["attempts"] == 2
    assert (
        "contradicts verified complete Git diff evidence"
        in transport.calls[1]["prompt"]
    )


def test_correction_loop_metadata_cannot_be_reported_as_product_finding():
    self_referential = valid_review(
        decision="BLOCKED", critical=["Review summary contains prompt leakage."]
    )
    self_referential["summary"] = (
        "The previous response requires the operator to re-run the AI model."
    )
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(self_referential)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert "correction-loop metadata" in transport.calls[1]["prompt"]


def test_pass_with_placeholder_high_findings_is_retried():
    placeholder = valid_review(high=["High finding 1"])
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(placeholder)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert "generic placeholder findings" in transport.calls[1]["prompt"]


def test_compact_numbered_placeholders_are_retried():
    placeholder = valid_review(decision="BLOCKED")
    placeholder["missing_requirements"] = ["missing_requirement1"]
    placeholder["security_findings"] = ["security_finding1"]
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(placeholder)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert "generic placeholder findings" in transport.calls[1]["prompt"]


def test_required_human_approval_is_retried_and_model_must_return_pass():
    human_gate = valid_review(decision="BLOCKED")
    human_gate["summary"] = "The code modification is not approved by a human reviewer."
    human_gate["medium_findings"] = [
        "Human approval is required before the later release gate."
    ]
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(human_gate)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert result["gate_state"] == "WAITING_HUMAN_APPROVAL"
    assert result["review"]["decision"] == "PASS"
    assert result["attempts"] == 2
    assert "expected safety invariant" in transport.calls[1]["prompt"]


def test_blocked_only_by_human_approval_stays_blocked_when_retries_exhausted():
    payload = valid_review(decision="BLOCKED")
    payload["summary"] = "Human approval is required before the later release gate."
    result = run_gate(
        FakeTransport([TransportResult(True, response=json.dumps(payload))]), retries=1
    )
    assert result["status"] == "BLOCKED"
    assert result["gate_state"] == "BLOCKED"
    assert result["schema_valid"] is False


def test_technical_finding_is_not_removed_when_it_mentions_human_approval():
    payload = valid_review(
        decision="BLOCKED",
        high=["SQL injection remains unsafe; human approval is required."],
    )
    result = run_gate(
        FakeTransport([TransportResult(True, response=json.dumps(payload))]), retries=1
    )
    assert result["status"] == "BLOCKED"
    assert payload["high_findings"][0] in result["review"]["high_findings"]


def test_safe_gate_assertions_are_not_treated_as_findings():
    payload = valid_review(decision="BLOCKED")
    payload["summary"] = "Human approval remains required at the later review gate."
    payload["missing_requirements"] = ["human_approval_required=true"]
    payload["security_findings"] = [
        "approval_bypass_detected=false",
        "auto_merge=false",
        "auto_deploy=false",
    ]
    payload["medium_findings"] = [
        "The implementation contains tests that verify the gate would block."
    ]
    payload["critical_findings"] = ["auto_merge=false"]
    payload["high_findings"] = ["There are findings that require manual review."]

    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(payload)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )
    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert result["review"]["decision"] == "PASS"
    assert all(
        result["review"][field] == []
        for field in (
            "missing_requirements",
            "security_findings",
            "medium_findings",
            "critical_findings",
            "high_findings",
        )
    )


def test_hyphenated_human_approval_requires_model_retry():
    payload = valid_review(decision="BLOCKED")
    payload["summary"] = (
        "A human-approval finding requires manual verification at the later gate."
    )
    payload["medium_findings"] = [
        "The human-approval finding requires manual verification."
    ]
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(payload)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )
    result = run_gate(transport, retries=2)
    assert result["status"] == "PASS"
    assert result["review"]["medium_findings"] == []


def test_ambiguous_unsafe_summary_is_not_normalized_to_pass():
    payload = valid_review(decision="BLOCKED")
    payload["summary"] = "The implementation is not safe and requires human approval."
    result = run_gate(
        FakeTransport([TransportResult(True, response=json.dumps(payload))]), retries=1
    )
    assert result["status"] == "BLOCKED"


def test_approval_bypass_finding_is_preserved_and_blocked():
    payload = valid_review()
    payload["security_findings"] = [
        "scripts/release.py execute_release() can execute a protected action before human approval."
    ]
    payload["safety_gates"]["approval_bypass_detected"] = True

    result = run_gate(
        FakeTransport([TransportResult(True, response=json.dumps(payload))]), retries=1
    )

    assert result["status"] == "BLOCKED"
    assert payload["security_findings"][0] in result["review"]["security_findings"]
    assert "Approval bypass was detected." in result["review"]["security_findings"]


def test_generic_approval_bypass_claim_is_retried_not_removed():
    generic = valid_review(decision="BLOCKED")
    generic["safety_gates"]["approval_bypass_detected"] = True
    generic["security_findings"] = ["Approval bypass was detected."]
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(generic)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert result["attempts"] == 2
    assert "lacks concrete implementation evidence" in transport.calls[1]["prompt"]


def test_bypass_finding_cannot_contradict_safe_gate():
    contradictory = valid_review(
        decision="BLOCKED", critical=["Approval bypass was detected."]
    )
    transport = FakeTransport(
        [
            TransportResult(True, response=json.dumps(contradictory)),
            TransportResult(True, response=json.dumps(valid_review())),
        ]
    )

    result = run_gate(transport, retries=2)

    assert result["status"] == "PASS"
    assert "contradicts its approval_bypass_detected" in transport.calls[1]["prompt"]


def test_auto_merge_enabled_is_blocked():
    payload = valid_review()
    payload["safety_gates"]["auto_merge"] = True
    result = run_gate(
        FakeTransport([TransportResult(True, response=json.dumps(payload))]), retries=1
    )
    assert result["status"] == "BLOCKED"
    assert "Automatic merge was enabled." in result["review"]["security_findings"]


def test_auto_deploy_enabled_is_blocked():
    payload = valid_review()
    payload["safety_gates"]["auto_deploy"] = True
    result = run_gate(
        FakeTransport([TransportResult(True, response=json.dumps(payload))]), retries=1
    )
    assert result["status"] == "BLOCKED"
    assert "Automatic deployment was enabled." in result["review"]["security_findings"]


@pytest.mark.parametrize(
    "field",
    [
        "merge_authorized",
        "release_authorized",
        "deployment_authorized",
        "production_authorized",
    ],
)
def test_any_ai_authorization_field_enabled_is_blocked(field):
    payload = valid_review()
    payload["safety_gates"][field] = True

    result = run_gate(
        FakeTransport([TransportResult(True, response=json.dumps(payload))]), retries=1
    )

    assert result["status"] == "BLOCKED"
    assert any("was granted by the AI reviewer" in item for item in result["review"]["security_findings"])


def test_missing_authorization_field_is_schema_invalid_and_blocked():
    payload = valid_review()
    payload["safety_gates"].pop("release_authorized")

    result = run_gate(
        FakeTransport([TransportResult(True, response=json.dumps(payload))] * 3),
        retries=3,
    )

    assert result["status"] == "BLOCKED"
    assert result["schema_valid"] is False


def test_endpoint_reachable_with_empty_model_list_does_not_imply_model_available():
    result = run_gate(
        FakeTransport(
            [
                TransportResult(
                    False,
                    error="model missing",
                    error_type="model_missing",
                    endpoint_reachable=True,
                    model_list_received=True,
                    model_available=False,
                )
            ]
        ),
        retries=1,
    )

    assert result["ollama"]["endpoint_reachable"] is True
    assert result["ollama"]["model_list_received"] is True
    assert result["ollama"]["model_available"] is False


def test_model_must_confirm_every_production_chunk_id():
    evidence = review_evidence()
    patch = (
        "diff --git a/app/service.py b/app/service.py\n"
        "--- a/app/service.py\n+++ b/app/service.py\n@@ -1 +1 @@\n-old\n+safe\n"
    )
    evidence["actual_git_diff"] = {
        "sha256": "f" * 64,
        "changed_files": ["M\tapp/service.py"],
        "stat": "1 file changed",
        "patch_preview": patch,
    }
    evidence["review_v3"] = build_review_v3_evidence(
        ["M\tapp/service.py"], patch, evidence["test_result_hashes"]
    )
    payload = valid_review()
    payload["reviewed_chunk_ids"] = evidence["review_v3"]["expected_chunk_ids"]

    result = run_gate(
        FakeTransport([TransportResult(True, response=json.dumps(payload))]),
        evidence=evidence,
        retries=1,
    )

    assert result["status"] == "PASS"
    assert result["evidence"]["full_diff_coverage"] is True


def test_missing_model_chunk_confirmation_remains_blocked():
    evidence = review_evidence()
    patch = (
        "diff --git a/app/service.py b/app/service.py\n"
        "--- a/app/service.py\n+++ b/app/service.py\n@@ -1 +1 @@\n-old\n+safe\n"
    )
    evidence["actual_git_diff"]["changed_files"] = ["M\tapp/service.py"]
    evidence["review_v3"] = build_review_v3_evidence(["M\tapp/service.py"], patch)
    payload = valid_review()

    result = run_gate(
        FakeTransport([TransportResult(True, response=json.dumps(payload))] * 3),
        evidence=evidence,
        retries=3,
    )

    assert result["status"] == "BLOCKED"
    assert result["schema_valid"] is False


def test_malformed_safety_gates_is_blocked():
    payload = valid_review()
    payload["safety_gates"].pop("approval_bypass_detected")
    result = run_gate(
        FakeTransport([TransportResult(True, response=json.dumps(payload))] * 3),
        retries=3,
    )
    assert result["status"] == "BLOCKED"
    assert result["schema_valid"] is False
    assert result["attempts"] == 3


def test_valid_pass_preserves_required_human_approval_gate():
    result = run_gate(
        FakeTransport([TransportResult(True, response=json.dumps(valid_review()))]),
        retries=1,
    )
    assert result["status"] == "PASS"
    assert result["gate_state"] == "WAITING_HUMAN_APPROVAL"
    assert result["review"]["safety_gates"] == {
        "human_approval_required": True,
        "auto_merge": False,
        "auto_deploy": False,
        "approval_bypass_detected": False,
        "merge_authorized": False,
        "release_authorized": False,
        "deployment_authorized": False,
        "production_authorized": False,
    }
    assert result["ollama"] == {
        "url": "http://localhost:11434",
        "model": "llama3",
        "endpoint_reachable": True,
        "model_list_received": True,
        "model_available": True,
        "response_received": True,
        "schema_valid": True,
        "installed_models": [],
        "model_digest": "e" * 64,
        "family": "llama",
        "ollama_version": "0.11.0-test",
        "prompt_version": PROMPT_VERSION,
        "context_tokens": review_context_tokens(),
        "temperature": 0.0,
        "num_predict": 1200,
        "error": "",
        "response": json.dumps(valid_review()),
    }


@pytest.mark.parametrize(
    "decision,expected_gate",
    [
        ("PASS", "WAITING_HUMAN_APPROVAL"),
        ("WARNING", "WAITING_HUMAN_REVIEW"),
        ("BLOCKED", "BLOCKED"),
    ],
)
def test_review_decisions_map_to_explicit_gate_states(decision, expected_gate):
    payload = valid_review(decision)
    if decision == "BLOCKED":
        payload["safety_gates"]["approval_bypass_detected"] = True
        payload["high_findings"] = [
            "release.py execute() can run a protected action before human approval."
        ]
    transport = FakeTransport([TransportResult(True, response=json.dumps(payload))])

    result = run_gate(transport)

    assert result["status"] == decision
    assert result["gate_state"] == expected_gate
    assert result["review_completed"] is True
    assert result["fallback_used"] is False


@pytest.mark.parametrize("field", ["critical_findings", "high_findings"])
def test_critical_or_high_finding_overrides_model_pass(field):
    payload = valid_review()
    payload[field] = ["Unsafe bypass detected."]

    result = run_gate(
        FakeTransport([TransportResult(True, response=json.dumps(payload))])
    )

    assert result["status"] == "BLOCKED"
    assert result["gate_state"] == "BLOCKED"


def test_ai_cannot_waive_human_review():
    payload = valid_review()
    payload["requires_human_review"] = False

    result = run_gate(
        FakeTransport([TransportResult(True, response=json.dumps(payload))]), retries=1
    )

    assert result["status"] == "BLOCKED"
    assert "AI cannot waive human review" in result["issues"][0]


def test_optional_mode_or_fallback_never_turns_offline_review_into_pass():
    result = run_gate(
        FakeTransport(
            [TransportResult(False, error="offline", error_type="unavailable")]
        ),
        retries=1,
        required=False,
    )

    assert result["status"] == "BLOCKED"
    assert result["fallback_used"] is False


def test_actual_git_diff_is_mandatory_and_is_sent_to_reviewer():
    incomplete = review_evidence()
    incomplete["actual_git_diff"] = {}
    transport = FakeTransport(
        [TransportResult(True, response=json.dumps(valid_review()))]
    )

    blocked = run_gate(transport, evidence=incomplete)

    assert blocked["status"] == "BLOCKED"
    assert transport.calls == []

    valid_transport = FakeTransport(
        [TransportResult(True, response=json.dumps(valid_review()))]
    )
    passed = run_gate(valid_transport)
    assert passed["status"] == "PASS"
    assert "docs/spec.md" in valid_transport.calls[0]["prompt"]
    assert "cccccccc" in valid_transport.calls[0]["prompt"]


def test_n8n_does_not_advance_from_successful_process_without_pass_gate(monkeypatch):
    calls = []

    def fake_run_command(args, timeout=900):
        calls.append(args)
        if "phase_validator.py" in args:
            return {
                "returncode": 0,
                "stdout_tail": json.dumps({"status": "PASS"}),
                "status": "PASS",
            }
        if any(str(arg).endswith("run_phase_review.py") for arg in args):
            return {
                "returncode": 0,
                "stdout_tail": json.dumps({"status": "BLOCKED", "decision": "PASS"}),
                "status": "PASS",
            }
        return {
            "returncode": 0,
            "stdout_tail": json.dumps({"status": "BLOCKED"}),
            "status": "PASS",
        }

    monkeypatch.setattr(n8n_phase_trigger, "run_command", fake_run_command)

    result = n8n_phase_trigger.run_local_controller("AI-05")

    assert result["status"] == "CORRECTION_REQUIRED"
    assert result["status"] != "WAITING_HUMAN_APPROVAL"


def test_ai_factory_does_not_advance_from_exit_code_alone(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location(
        "mandatory_factory_runner", PROJECT_ROOT / "ai-factory" / "run_ai_factory.py"
    )
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    def fake_run_command(args, timeout=900):
        if any(str(arg).endswith("run_phase_review.py") for arg in args):
            stdout = json.dumps({"status": "BLOCKED", "decision": "PASS"})
        else:
            stdout = json.dumps({"status": "PASS"})
        return {
            "command": "test",
            "returncode": 0,
            "duration_seconds": 0,
            "stdout_tail": stdout,
            "stderr_tail": "",
            "status": "PASS",
        }

    monkeypatch.setattr(runner, "run_command", fake_run_command)
    monkeypatch.setattr(
        runner, "build_evidence_package", lambda **kwargs: {"phase": "AI-05"}
    )
    monkeypatch.setattr(
        runner, "generate_final_report", lambda: {"decision": "BLOCKED"}
    )
    monkeypatch.setattr(runner, "DEFAULT_RESULT", tmp_path / "factory.json")

    result = runner.run_factory("AI-05")

    assert result["status"] == "AI_SOFTWARE_FACTORY_BLOCKED"
    assert result["review_gate_passed"] is False
