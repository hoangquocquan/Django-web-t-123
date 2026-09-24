# AI-05 Correction History

## Engineering Iterations

1. Added strict JSON Schema after `llama3` returned nested `review`/`safety` output.
2. Locked model/prompt metadata and rejected prompt leakage and deployment authorization.
3. Separated system instructions from untrusted Git evidence with Ollama `/api/chat`.
4. Preserved complete JSON by truncating only the patch projection, then rejected placeholder and deterministic-result contradictions.
5. Separated technical verdict from the later human approval gate.

The engineering loop exceeded the master guideline of three phase-level correction attempts. This process deviation is one reason the phase is not marked PASS.

## Final Mandatory Review Execution

- Attempts allowed: 3.
- Attempt 1: rejected because human-approval gate metadata was reported as a technical finding.
- Attempt 2: same semantic contradiction.
- Attempt 3: same semantic contradiction.
- Final result: `BLOCKED`.
- Fallback: not used.
- External AI: not used.
