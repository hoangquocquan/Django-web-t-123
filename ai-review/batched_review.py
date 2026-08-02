"""Fail-closed batching for cumulative mandatory Ollama reviews."""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from mandatory_review import run_mandatory_review, safety_payload
from review_v3 import (
    create_artifact_manifest,
    sha256_text,
    signature_status,
    validate_review_v3_evidence,
    write_json,
)


def build_batches(review_v3, max_chars=28000, max_chunks=16):
    """Chia chunk theo thứ tự ổn định và không bỏ sót ID nào."""
    batches = []
    current = []
    current_chars = 0
    for chunk in review_v3.get("production_chunks", []):
        chunk_chars = len(str(chunk.get("content", "")))
        if current and (
            len(current) >= max_chunks or current_chars + chunk_chars > max_chars
        ):
            batches.append(current)
            current, current_chars = [], 0
        current.append(copy.deepcopy(chunk))
        current_chars += chunk_chars
    if current:
        batches.append(current)
    return batches


def make_batch_evidence(evidence, chunks, batch_number, batch_count):
    """Tạo evidence tự đủ cho một batch code production."""
    result = copy.deepcopy(evidence)
    source_v3 = evidence["review_v3"]
    paths = list(dict.fromkeys(chunk["path"] for chunk in chunks))
    chunk_ids = [chunk["id"] for chunk in chunks]
    result["phase_specification"]["content"] += (
        f"\n\nCUMULATIVE REVIEW BATCH {batch_number}/{batch_count}: "
        "review every supplied production chunk; do not infer coverage outside this batch."
    )
    result["actual_git_diff"] = {
        "sha256": sha256_text(
            json.dumps(
                {
                    "source": evidence["actual_git_diff"]["sha256"],
                    "batch": batch_number,
                    "chunks": [(chunk["id"], chunk["sha256"]) for chunk in chunks],
                },
                sort_keys=True,
            )
        ),
        "changed_files": [f"M\t{path}" for path in paths],
        "stat": f"cumulative review batch {batch_number}/{batch_count}",
        "patch_preview": "",
    }
    result["review_v3"] = {
        "version": "review-v3",
        "changed_files": [
            {"status": "M", "path": path, "classification": "production"}
            for path in paths
        ],
        "production_files": paths,
        "production_chunks": chunks,
        "expected_chunk_ids": chunk_ids,
        "skipped_files": source_v3.get("skipped_files", []),
        "unreviewed_production_files": [],
        "test_contract": source_v3["test_contract"],
        "documentation_contract": source_v3["documentation_contract"],
        "blockers": [],
        "full_diff_coverage": True,
        "status": "PASS",
    }
    result["batch"] = {
        "number": batch_number,
        "count": batch_count,
        "source_diff_sha256": evidence["actual_git_diff"]["sha256"],
        "chunk_ids": chunk_ids,
    }
    return result


def make_aggregate_evidence(evidence, batch_results):
    """Tạo input tổng hợp nhỏ từ các PASS do model trả về cho từng batch."""
    result = copy.deepcopy(evidence)
    source_v3 = evidence["review_v3"]
    aggregate_chunks = []
    for chunk in source_v3["production_chunks"]:
        content = (
            f"[MODEL_REVIEWED_BATCH_ATTESTATION id={chunk['id']} "
            f"source_sha256={chunk['sha256']}]"
        )
        aggregate_chunks.append(
            {
                "id": chunk["id"],
                "path": chunk["path"],
                "index": chunk["index"],
                "sha256": sha256_text(content),
                "source_sha256": chunk["sha256"],
                "content": content,
            }
        )
    result["phase_specification"]["content"] += (
        "\n\nCUMULATIVE AGGREGATION: every production chunk below has a schema-valid "
        "local model PASS attestation. Verify the complete ID set and safety gates."
    )
    result["review_v3"] = {
        **copy.deepcopy(source_v3),
        "production_chunks": aggregate_chunks,
        "expected_chunk_ids": [chunk["id"] for chunk in aggregate_chunks],
        "blockers": [],
        "unreviewed_production_files": [],
        "full_diff_coverage": True,
        "status": "PASS",
    }
    result["batch_attestations"] = [
        {
            "batch": index,
            "status": item["status"],
            "review_output_sha256": item.get("evidence", {}).get(
                "review_output_sha256", ""
            ),
            "reviewed_chunk_ids": item.get("evidence", {}).get(
                "reviewed_chunk_ids", []
            ),
            "model_digest": item.get("ollama", {}).get("model_digest", ""),
        }
        for index, item in enumerate(batch_results, start=1)
    ]
    return result


def blocked_batch_result(reason, batch_results):
    """Không cho aggregate PASS khi một batch thiếu hoặc bị chặn."""
    return {
        "status": "BLOCKED",
        "gate_state": "BLOCKED",
        "review_completed": False,
        "schema_valid": False,
        "fallback_used": False,
        "summary": reason,
        "issues": [reason],
        "batch_review": {
            "status": "BLOCKED",
            "completed_batches": len(batch_results),
            "results": batch_results,
        },
        "safety": safety_payload(),
    }


def run_batched_review(
    evidence,
    rules,
    tests,
    reviewer=run_mandatory_review,
    transport=None,
    model="llama3",
    url="http://localhost:11434",
    timeout=120,
    max_retries=3,
    max_chars=28000,
    max_chunks=16,
):
    """Review every batch, then ask the model for a final aggregate decision."""
    coverage_errors = validate_review_v3_evidence(evidence.get("review_v3") or {})
    if coverage_errors:
        return blocked_batch_result("; ".join(coverage_errors), [])
    batches = build_batches(evidence["review_v3"], max_chars, max_chunks)
    if not batches:
        batches = [[]]
    batch_results = []
    reviewed_ids = []
    for index, chunks in enumerate(batches, start=1):
        batch_evidence = make_batch_evidence(evidence, chunks, index, len(batches))
        result = reviewer(
            evidence=batch_evidence,
            rules=rules,
            tests=tests,
            transport=transport,
            required=True,
            model=model,
            url=url,
            timeout=timeout,
            max_retries=max_retries,
        )
        batch_results.append(result)
        if result.get("status") != "PASS":
            return blocked_batch_result(f"Cumulative review batch {index} blocked.", batch_results)
        reviewed_ids.extend(result.get("evidence", {}).get("reviewed_chunk_ids", []))
    expected_ids = evidence["review_v3"]["expected_chunk_ids"]
    if reviewed_ids != expected_ids:
        return blocked_batch_result(
            "Cumulative batch coverage does not match the expected chunk order.",
            batch_results,
        )
    aggregate_evidence = make_aggregate_evidence(evidence, batch_results)
    aggregate_tests = copy.deepcopy(tests)
    aggregate_tests["batch_attestations"] = aggregate_evidence["batch_attestations"]
    final = reviewer(
        evidence=aggregate_evidence,
        rules=rules,
        tests=aggregate_tests,
        transport=transport,
        required=True,
        model=model,
        url=url,
        timeout=timeout,
        max_retries=max_retries,
    )
    final["batch_review"] = {
        "status": "PASS" if final.get("status") == "PASS" else "BLOCKED",
        "batch_count": len(batches),
        "source_chunk_count": len(expected_ids),
        "reviewed_chunk_count": len(reviewed_ids),
        "source_diff_sha256": evidence["actual_git_diff"]["sha256"],
        "results": batch_results,
    }
    return final


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Run cumulative REVIEW-V3 in local Ollama batches.")
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--rules", required=True)
    parser.add_argument("--tests", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--batch-dir", required=True)
    parser.add_argument("--model", default=os.getenv("AI_REVIEW_MODEL", "llama3"))
    parser.add_argument("--url", default=os.getenv("OLLAMA_URL", "http://localhost:11434"))
    args = parser.parse_args()
    evidence = load_json(args.evidence)
    result = run_batched_review(
        evidence,
        load_json(args.rules),
        load_json(args.tests),
        model=args.model,
        url=args.url,
        timeout=int(os.getenv("AI_REVIEW_TIMEOUT_SECONDS", "120")),
        max_retries=int(os.getenv("AI_REVIEW_MAX_RETRIES", "3")),
    )
    output = Path(args.output)
    batch_dir = Path(args.batch_dir)
    batch_dir.mkdir(parents=True, exist_ok=True)
    batch_paths = []
    for index, batch_result in enumerate(
        result.get("batch_review", {}).get("results", []), start=1
    ):
        batch_path = batch_dir / f"batch-{index:02d}.json"
        write_json(batch_path, batch_result)
        batch_paths.append(batch_path)
    manifest_path = output.with_name(output.stem + "_artifact_manifest.json")
    result["artifact_manifest"] = {
        "path": str(manifest_path),
        "signature_status": signature_status(),
    }
    write_json(output, result)
    ollama = result.get("ollama") or {}
    manifest = create_artifact_manifest(
        phase=evidence.get("phase", "unknown"),
        base_commit=evidence.get("git", {}).get("base_commit", ""),
        current_commit=evidence.get("git", {}).get("current_commit", ""),
        review_v3=evidence.get("review_v3") or {},
        artifact_paths=[args.evidence, args.rules, args.tests, output, *batch_paths],
        model_identity={
            "model": ollama.get("model", args.model),
            "model_digest": ollama.get("model_digest", ""),
            "family": ollama.get("family", ""),
            "prompt_version": ollama.get("prompt_version", ""),
            "context_tokens": ollama.get("context_tokens"),
            "temperature": ollama.get("temperature"),
            "num_predict": ollama.get("num_predict"),
            "ollama_version": ollama.get("ollama_version", ""),
        },
        correlation_id=evidence.get("correlation_id", ""),
    )
    write_json(manifest_path, manifest)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
