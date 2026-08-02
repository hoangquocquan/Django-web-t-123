# PROD-01 Business UI And UAT Review

## Phase

- Date: 2026-08-02
- Branch: `codex/production-readiness-full`
- Baseline: `da5030ee1ac69d2eb21d666a562d249064736a28`
- Phase commit: `6ce0dd43136dc5c3591b9a8467448fd97939dbb9`
- Decision: `PASS_WITH_WARNINGS`
- Next-phase eligibility: `READY_FOR_NEXT_PHASE`

## Objective And Scope

PROD-01 replaced the shared `dashboard:read` page gate with module-specific
permissions, completed the Sales and CRM browser workflows, enforced a separate
human quotation approval permission, and rendered AI output as structured UI.

## Architecture And Database Impact

- Business UI GET/POST controllers now enforce Foundation permissions for the
  actual owning module.
- Sales workflow writes go through `SalesPlatformService`; approval and handoff
  use database transactions and audit activities.
- Migration `foundation.0005` adds `sales:approve` and grants it only to the
  admin role. Existing business data and legacy tables are not changed.
- Kanban columns are bounded to the latest 25 records per status, reducing the
  tested page response from about 32 MB to 667 KB.

## Security Impact

- Missing module access returns HTTP 403 and CSRF remains mandatory.
- `sales:write` cannot approve a quotation; `sales:approve` is required.
- Handoff is rejected until approval exists.
- Server-side validation rejects blank required values and invalid monetary
  values even when browser validation is bypassed.
- No credential, runtime database, ZIP, PII log, or backup is staged.

## Validation Results

- Compile, Django check, and migration drift: PASS.
- PROD-01 focused/integration tests: 15 passed.
- Mandatory-review correction plus focused tests: 67 passed.
- Full regression after correction: 462 passed.
- Chrome Selenium E2E: PASS.
- Project dependency audit: no known vulnerabilities.
- Bandit: 0 Critical/High/Medium; one Low false-positive session-key name.
- Targeted mypy: PASS with missing Django stubs and one inherited dynamic
  manager diagnostic excluded and documented.

## Mandatory Ollama Review

- Model: `llama3`
- Decision: PASS
- Schema valid: true
- Fallback used: false
- Critical/High findings: 0/0
- Attempts: 2
- Correction: the first response claimed the phase was ready for deployment.
  The fail-closed detector and regression test were hardened; the corrected
  response contains no deployment authorization.
- Gate state: `WAITING_HUMAN_APPROVAL`.

## Runtime Warnings

Docker daemon, PostgreSQL, Redis, and live n8n are not verified in this phase.
They are not PROD-01 dependencies, are not claimed as operational, and remain
explicit gates for PROD-02 and PROD-04.

## Rollback

Revert the dedicated PROD-01 implementation commit. Do not reset the branch,
delete user ZIP files, or alter the ignored local development database.

## Final Decision

`PASS_WITH_WARNINGS`. The Business UI/UAT objective is met and PROD-02 may start.
This decision does not authorize merge, push, tag, staging, or production deploy.
