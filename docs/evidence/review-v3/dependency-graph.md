# REVIEW-V3 Dependency Graph

```text
Git staged diff
  -> evidence_collector.py
     -> review_v3.py (inventory, chunks, contracts, SHA-256)
  -> mandatory_review.py
     -> deterministic REVIEW-V3 validation
     -> LocalOllamaReviewTransport
        -> local /api/tags
        -> local /api/version
        -> local /api/chat
  -> ollama_phase_reviewer.py
     -> result JSON
     -> artifact manifest
  -> human approval gate
```

PROD-06 depends on a committed, schema-valid REVIEW-V3 `PASS`. PROD-07 depends on both REVIEW-V3 and PROD-06 passing.
