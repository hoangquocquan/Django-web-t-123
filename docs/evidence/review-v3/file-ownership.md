# REVIEW-V3 File Ownership

- `ai-review/mandatory_review.py`: mandatory decision, consistency, transport, and fail-closed gate.
- `ai-review/review_v3.py`: deterministic diff coverage, test/docs contracts, hashes, and manifest.
- `ai-review/evidence_collector.py`: read-only Git and phase evidence collection.
- `ai-review/ollama_phase_reviewer.py`: mandatory review CLI and artifact packaging.
- `scripts/ollama_phase_reviewer.py`: local-only Ollama HTTP transport helpers.
- `tests/test_ai_mandatory_review_gate.py`: mandatory gate regression contract.
- `tests/test_review_engine_v3.py`: focused REVIEW-V3 coverage and security contract.
