# REVIEW-V3 Mandatory Ollama Review Engine Hardening

## Objective

Harden the mandatory local Ollama reviewer so every production diff chunk is covered, deterministic test and documentation contracts are enforced, transport and model identity are explicit, and no code path converts a model `BLOCKED` decision directly into `PASS`.

## Required Safety Gates

The model must return all fields below. Human approval remains required and every authorization field remains false.

```json
{
  "human_approval_required": true,
  "auto_merge": false,
  "auto_deploy": false,
  "approval_bypass_detected": false,
  "merge_authorized": false,
  "release_authorized": false,
  "deployment_authorized": false,
  "production_authorized": false
}
```

## Implementation Requirements

- Retry a model response that blocks only because later human approval is required; never rewrite that decision to `PASS`.
- Inventory and classify every changed file. Hash every production chunk with SHA-256 and reject missing or mismatched coverage.
- Summarize changed tests and documentation deterministically without sending their raw bodies to the model.
- Block removed security assertions, unsafe skip/xfail changes, and documentation that enables automatic merge or deployment.
- Record explicit Ollama transport facts, selected model identity, deterministic generation options, and Ollama version.
- Produce an artifact manifest with hashes and an honest signature status.
- Preserve fail-closed behavior for unavailable Ollama, malformed JSON, schema mismatch, inconsistent findings, missing coverage, or unsafe authorization.

## Validation Gate

Focused REVIEW-V3 tests, Django checks, migration drift checks, the complete regression suite, static/security checks, and a real schema-valid local Ollama `PASS` are required before PROD-06 can be revalidated. No merge, push, tag, deployment, or production authorization is allowed.
