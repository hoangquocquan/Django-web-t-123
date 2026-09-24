# REVIEW-V3 Validation Matrix

| Gate | Result | Evidence / reason |
|---|---|---|
| Compile | PASS | Five changed Python source files compiled. |
| Django check | PASS | Zero issues. |
| Migration drift | PASS | No changes detected. |
| Focused tests | PASS | 82 passed. |
| Integration/regression | PASS | 538 passed. |
| E2E | NOT_RUN | REVIEW-V3 changes an internal review gate, not a user workflow; regression and real Ollama execution cover the affected path. |
| Security audit | PASS | Bandit returned zero findings; external Ollama endpoints are rejected. |
| Type audit | PASS | Mypy found no issues in five changed source files. |
| Docker | NOT_RUN | No container/runtime artifact changed; no impact on REVIEW-V3 decision. |
| PostgreSQL | NOT_RUN | No model, migration, query, or database configuration changed. |
| Redis | NOT_RUN | No cache/session behavior changed. |
| n8n | NOT_RUN | No orchestration workflow changed; mandatory gate integration remains covered by regression tests. |
| Ollama transport | PASS | Endpoint, model list, model, response, and schema facts are explicit. |
| Real Ollama review | PASS | Attempt 1, local `llama3`, no fallback, 22/22 chunks. |
| Artifact manifest | PASS | All listed hashes verified. |
| Signature | NOT_RUN | `SIGNATURE_NOT_AVAILABLE`; no signature was claimed. |
