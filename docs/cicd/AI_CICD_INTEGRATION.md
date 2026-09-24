# AI CI/CD Integration

## Purpose

AI assists the CI/CD workflow by summarizing phase validation, identifying risks,
and preparing review material. It does not replace human approval.

## Ollama Review Point

Ollama should run after:

1. Source checkout.
2. Artifact/document validation.
3. Tests.
4. Security checks.

Inputs:

- Phase prompt.
- Changed file list.
- Validator output.
- Test summary.
- Review summary.

Outputs:

- AI review report.
- Risk summary.
- Suggested decision: `PASS`, `PASS_WITH_WARNING`, or `BLOCKED`.

## n8n Orchestration Point

n8n can orchestrate:

- Manual workflow trigger.
- Phase validator execution.
- Test execution.
- Ollama reviewer execution.
- Notification to reviewer.

n8n must not:

- deploy production automatically
- create production secrets
- approve production
- merge protected branches

## Human Approval Boundary

Required human approval:

- merge to protected branches
- release candidate approval
- staging promotion
- production deployment
- rollback execution

AI can recommend. Humans decide.

## Failure Handling

If Ollama is unavailable:

- CI should continue with `PASS_WITH_WARNING` only if required tests pass.
- Review summary must state AI review was limited.
- Human review remains mandatory.

