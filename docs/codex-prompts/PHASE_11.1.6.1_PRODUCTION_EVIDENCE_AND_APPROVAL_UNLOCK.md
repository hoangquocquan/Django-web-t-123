# Phase 11.1.6.1 - Production Evidence And Approval Unlock

## Project

mecprecision-vietnam

## Objective

Collect final production evidence and complete the approval package required to
unlock Legacy API shutdown execution.

Target transition:

```text
BLOCKED_SAFELY
```

to:

```text
READY_TO_EXECUTE
```

## Important Rules

Do not:

- Disable Legacy API.
- Change routes.
- Modify IIS.
- Modify database.
- Execute shutdown.

Only:

- Collect evidence.
- Validate evidence.
- Complete approval package.
- Prepare execution authorization.

## Required Documents

- `docs/reviews/PHASE_11.1.6_REVIEW_SUMMARY.md`
- `docs/migration/production_evidence/`
- `docs/migration/LEGACY_API_DECOMMISSION_EXECUTION_RUNBOOK.md`
- `docs/migration/LEGACY_API_POST_SHUTDOWN_MONITORING.md`
- `docs/migration/IIS_PRODUCTION_EVIDENCE_DEPLOYMENT_GUIDE.md`

## Implementation Tasks

1. Create `scripts/phase11_1_6_1_final_evidence_validator.py`.
2. Create final approval templates under `docs/migration/phase11_1_6_execution/approvals/`.
3. Create `scripts/phase11_1_6_1_approval_validator.py`.
4. Create `docs/reviews/PHASE_11.1.6.1_UNLOCK_REVIEW.md`.
5. Update `docs/migration/LEGACY_API_DECOMMISSION_EXECUTION_RUNBOOK.md` with final unlock requirements.
6. Create `tests/test_phase11_1_6_1_unlock_validation.py`.

## Testing Requirements

Run:

```powershell
python scripts\phase11_1_6_1_final_evidence_validator.py
python scripts\phase11_1_6_1_approval_validator.py
pytest tests\test_phase11_1_6_1_unlock_validation.py
pytest
powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1
```

Expected local result without real approval:

```text
BLOCKED_SAFELY
```

Expected result with complete evidence and approval:

```text
READY_TO_EXECUTE
```

## Git Requirements

Branch:

```text
migration/phase-11.1.6.1-evidence-approval-unlock
```

Commit:

```text
feat: add legacy api shutdown unlock validation
```

Tag:

```text
phase-11.1.6.1-ready-to-execute
```

## Final Status

`WAITING_FOR_ARCHITECT REVIEW`

Do not start Phase 11.2 and do not execute Legacy API shutdown.
