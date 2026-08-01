# AI-05 Mandatory Ollama Phase Review

## Objective

Make local Ollama review a fail-closed technical gate for AI Factory and n8n. A subprocess exit code or fallback report must never be enough to advance a phase.

## Required Configuration

- `AI_REVIEW_REQUIRED=true`
- `AI_REVIEW_MODEL=llama3`
- `AI_REVIEW_TIMEOUT_SECONDS=120`
- `AI_REVIEW_MAX_RETRIES=3`
- `AI_REVIEW_PROMPT_VERSION=ai-review-v2.0`

## Review Evidence

The reviewer must receive the phase specification, base/current commit, actual Git patch and hash, changed files, migrations, tests and test-result hashes. Self-declared summaries alone are insufficient.

## Fail-Closed Rules

- Ollama unavailable, model missing, timeout, empty output, invalid JSON or schema mismatch: `BLOCKED`.
- Critical or High finding: `BLOCKED`, even if the model says PASS.
- WARNING: `WAITING_HUMAN_REVIEW`.
- PASS: `WAITING_HUMAN_APPROVAL`; it does not approve main merge or deployment.
- Fallback cannot return PASS.
- Model output cannot waive human review.
- Maximum correction/review attempts: three.

## n8n States

`CODEX_RUNNING`, `TESTING`, `AI_REVIEWING`, `CORRECTION_REQUIRED`, `WAITING_HUMAN_REVIEW`, `WAITING_HUMAN_APPROVAL`, `BLOCKED`, `FAILED`.

n8n cannot merge, deploy, approve or advance based only on an HTTP/process success code.

## Acceptance Criteria

- All required failure cases are covered by automated tests.
- AI Factory and n8n parse the review JSON contract and enforce `gate_state`.
- Actual staged Git diff is included in real local review evidence.
- Real local Ollama review returns valid schema with no Critical or High findings.
- Full regression suite passes.

## Rollback

Revert AI-05 commits. No database migration is created by this phase.

## Expected Commit

`feat(ai-factory): enforce mandatory ollama phase review`
