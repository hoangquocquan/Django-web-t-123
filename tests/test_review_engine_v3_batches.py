import copy
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = PROJECT_ROOT / "ai-review"
if str(REVIEW_DIR) not in sys.path:
    sys.path.insert(0, str(REVIEW_DIR))

from batched_review import build_batches, run_batched_review
from review_v3 import build_review_v3_evidence


def source_evidence(chunk_lines=100):
    body = "+" + ("safe_line\n+" * chunk_lines)
    patch = (
        "diff --git a/app/service.py b/app/service.py\n"
        "--- a/app/service.py\n+++ b/app/service.py\n@@ -1 +1 @@\n"
        + body
    )
    review_v3 = build_review_v3_evidence(["M\tapp/service.py"], patch)
    return {
        "phase": "PROD-07",
        "correlation_id": "batch-test",
        "phase_specification": {"path": "spec.md", "content": "Review all chunks."},
        "git": {"base_commit": "a" * 40, "current_commit": "b" * 40},
        "actual_git_diff": {
            "sha256": "c" * 64,
            "changed_files": ["M\tapp/service.py"],
            "stat": "1 file changed",
        },
        "review_v3": review_v3,
        "migrations": [],
        "test_result_hashes": {"tests.json": "d" * 64},
    }


def fake_pass(evidence, **_kwargs):
    ids = evidence["review_v3"]["expected_chunk_ids"]
    return {
        "status": "PASS",
        "gate_state": "WAITING_HUMAN_APPROVAL",
        "evidence": {
            "reviewed_chunk_ids": ids,
            "review_output_sha256": "e" * 64,
        },
        "ollama": {"model_digest": "f" * 64},
        "safety": {"human_approval_required": True},
    }


def test_batches_cover_every_chunk_in_original_order():
    evidence = source_evidence(900)
    batches = build_batches(evidence["review_v3"], max_chars=3000, max_chunks=2)

    ids = [chunk["id"] for batch in batches for chunk in batch]

    assert len(batches) > 1
    assert ids == evidence["review_v3"]["expected_chunk_ids"]


def test_batched_review_calls_final_aggregate_only_after_all_batches_pass():
    evidence = source_evidence(900)
    calls = []

    def reviewer(evidence, **kwargs):
        calls.append(copy.deepcopy(evidence))
        return fake_pass(evidence, **kwargs)

    result = run_batched_review(
        evidence,
        {"status": "PASS"},
        {"status": "PASS"},
        reviewer=reviewer,
        max_chars=3000,
        max_chunks=2,
    )

    assert result["status"] == "PASS"
    assert result["batch_review"]["reviewed_chunk_count"] == len(
        evidence["review_v3"]["expected_chunk_ids"]
    )
    assert "MODEL_REVIEWED_BATCH_ATTESTATION" in calls[-1]["review_v3"]["production_chunks"][0]["content"]


def test_one_blocked_batch_prevents_aggregate_review():
    evidence = source_evidence(900)
    calls = []

    def reviewer(evidence, **_kwargs):
        calls.append(evidence)
        if len(calls) == 2:
            return {"status": "BLOCKED", "evidence": {}, "ollama": {}}
        return fake_pass(evidence)

    result = run_batched_review(
        evidence,
        {"status": "PASS"},
        {"status": "PASS"},
        reviewer=reviewer,
        max_chars=3000,
        max_chunks=2,
    )

    assert result["status"] == "BLOCKED"
    assert result["gate_state"] == "BLOCKED"
    assert "batch 2 blocked" in result["summary"]


def test_malformed_source_coverage_blocks_before_model_call():
    evidence = source_evidence()
    evidence["review_v3"]["production_chunks"][0]["content"] += "tampered"
    calls = []

    result = run_batched_review(
        evidence,
        {"status": "PASS"},
        {"status": "PASS"},
        reviewer=lambda **kwargs: calls.append(kwargs),
    )

    assert result["status"] == "BLOCKED"
    assert calls == []


def test_batch_size_limits_are_deterministic():
    evidence = source_evidence(900)

    first = build_batches(evidence["review_v3"], max_chars=4000, max_chunks=3)
    second = build_batches(evidence["review_v3"], max_chars=4000, max_chunks=3)

    assert first == second
    assert all(len(batch) <= 3 for batch in first)
