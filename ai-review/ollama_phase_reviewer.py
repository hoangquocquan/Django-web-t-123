"""Mandatory fail-closed Ollama phase reviewer compatibility entrypoint."""

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
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from mandatory_review import production_language_detected, run_mandatory_review
from review_v3 import create_artifact_manifest, signature_status, write_json


__all__ = ["production_language_detected", "review_phase"]


DEFAULT_EVIDENCE = PROJECT_ROOT / "ai-review" / "evidence" / "current_phase.json"
DEFAULT_RULES = PROJECT_ROOT / "ai-review" / "results" / "rule_validation.json"
DEFAULT_TESTS = PROJECT_ROOT / "ai-review" / "results" / "test_result.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "ai-review" / "results" / "ai_review.json"
DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("AI_REVIEW_MODEL", os.getenv("OLLAMA_MODEL", "llama3"))


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path):
    target = Path(path)
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def normalize_status(ai_text):
    """Keep the legacy helper while normalizing to mandatory gate states."""
    text = str(ai_text or "").upper()
    if "BLOCKED" in text:
        return "BLOCKED"
    if "PASS_WITH_WARNING" in text or "WARNING" in text:
        return "WARNING"
    return "PASS" if "PASS" in text else "BLOCKED"


def review_phase(
    evidence_path=DEFAULT_EVIDENCE,
    rule_path=DEFAULT_RULES,
    test_path=DEFAULT_TESTS,
    output_path=None,
    ollama_url=DEFAULT_OLLAMA_URL,
    model=DEFAULT_MODEL,
    transport=None,
):
    """Require a real valid local review; no fallback can produce PASS."""
    required = os.getenv("AI_REVIEW_REQUIRED", "true").strip().casefold() in {"1", "true", "yes", "on"}
    timeout = int(os.getenv("AI_REVIEW_TIMEOUT_SECONDS", "120"))
    retries = min(3, max(1, int(os.getenv("AI_REVIEW_MAX_RETRIES", "3"))))
    evidence = load_json(evidence_path)
    result = run_mandatory_review(
        evidence=evidence,
        rules=load_json(rule_path),
        tests=load_json(test_path),
        transport=transport,
        required=required,
        model=model,
        url=ollama_url,
        timeout=timeout,
        max_retries=retries,
    )
    result.update({"phase": evidence.get("phase", "unknown"), "created_at": utc_now()})
    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = output.with_name(output.stem + "_artifact_manifest.json")
    result["artifact_manifest"] = {
        "path": str(manifest_path),
        "signature_status": signature_status(),
    }
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    ollama = result.get("ollama") or {}
    manifest = create_artifact_manifest(
        phase=evidence.get("phase", "unknown"),
        base_commit=(evidence.get("git") or {}).get("base_commit", ""),
        current_commit=(evidence.get("git") or {}).get("current_commit", ""),
        review_v3=evidence.get("review_v3") or {},
        artifact_paths=[evidence_path, rule_path, test_path, output],
        model_identity={
            "model": ollama.get("model", model),
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
    return result


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Run mandatory local Ollama phase review.")
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
    return 0 if result["status"] == "PASS" and result["gate_state"] == "WAITING_HUMAN_APPROVAL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
