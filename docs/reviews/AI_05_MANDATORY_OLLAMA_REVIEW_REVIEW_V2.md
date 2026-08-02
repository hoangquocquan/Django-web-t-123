# AI-05 Mandatory Ollama Review V2

## Decision

`PASS` with gate state `WAITING_HUMAN_APPROVAL`.

The real local Ollama review completed with a schema-valid response, no
fallback, and zero Critical or High findings. This technical result does not
approve merge, deployment, or production use.

## Changes

- Defines required human approval as a healthy safety invariant rather than a
  technical finding.
- Adds the strict `safety_gates` object and rejects missing, malformed, unknown,
  or unsafe gate values.
- Removes only findings that state the expected human-approval invariant;
  bypass, self-approval, automatic merge/deploy, and protected actions before
  approval remain blocking.
- Keeps invalid reviews fail-closed and limits correction attempts to three.
- Replaces ambiguous Ollama availability evidence with
  `endpoint_reachable`, `model_available`, `response_received`, and
  `schema_valid`.
- Uses a bounded review projection so test fixtures and embedded reviewer
  instructions cannot be mistaken for enabled production behavior.
- Gives the local reviewer an explicitly bounded 8,192-token context so the
  evidence and strict schema are not truncated by a small model default.

## Safety Gates

```json
{
  "human_approval_required": true,
  "auto_merge": false,
  "auto_deploy": false,
  "approval_bypass_detected": false
}
```

Fallback cannot produce `PASS`. A malformed review or unsafe gate remains
`BLOCKED`.

## Validation

- Django system check: PASS.
- Migration drift check: PASS (`No changes detected`).
- Focused AI review and compatibility tests: 85 passed.
- Full regression: 446 passed.
- Mypy: PASS, 3 changed source files checked.
- Bandit on changed Python files: 0 High, 0 Medium, 1 Low.
- The Low result is B105 on the workflow state string
  `WAITING_HUMAN_APPROVAL`, a non-secret false positive.

The repository-wide Bandit scan was also executed. It reported six inherited
Medium findings outside this AI-05 change: five SQL-construction warnings in
legacy ORM tests and one URL-scheme warning in the existing Django Ollama
client. AI-05 introduced none of them.

## Real Ollama Evidence

- Endpoint: `http://localhost:11434`
- Model: `llama3`
- Attempt: 1 of maximum 3
- `endpoint_reachable`: true
- `model_available`: true
- `response_received`: true
- `schema_valid`: true
- Decision: `PASS`
- Critical findings: 0
- High findings: 0
- Fallback used: false
- Review input SHA-256:
  `4f0f9a70231d8f45c1a9435ce450fa1619163ad5d6197128a66aa0465e3168e9`
- Review output SHA-256:
  `d3dea122a7466911463136660d6e80d0aa356ee4845446ac7ea141cfed4c73b7`
- Reviewed diff SHA-256:
  `2ea0e8fa3607e89b7724d59124bc7b867c038dd72dfab1d68a1ce2743cc583e0`

Machine-readable result:

`docs/reviews/AI_05_MANDATORY_OLLAMA_REVIEW_RESULT_V2.json`

## Impact And Rollback

There is no database migration and no business API change. The change is
limited to the local AI review contract, prompt, evidence semantics, report
rendering, configuration example, and tests.

Rollback is a Git revert of the dedicated AI-05 V2 commit. Human approval,
automatic merge, and automatic deployment remain unchanged during rollback.

## Next Gate

AI-05 is technically eligible for later human approval. AI-06 was not started
as part of this work.
