# Phase 11.1.6.3 - Legacy API Shutdown Approval Package Preparation

## Project

mecprecision-vietnam

## Objective

Prepare the formal approval package required before Legacy API shutdown
execution.

## Current State

```text
BLOCKED_SAFELY
```

Reason:

- Production evidence is incomplete.
- Approval package is incomplete.

## Important Rules

Do not:

- Execute shutdown.
- Disable Legacy API.
- Modify IIS.
- Modify routing.
- Modify database.
- Change production configuration.

Only:

- Create approval documents.
- Create validation checklist.
- Prepare governance package.

## Required Documents

- `docs/reviews/PHASE_11.1.6.1_UNLOCK_REVIEW.md`
- `docs/reviews/PHASE_11.1.6.2.2_IIS_DEBUG_REVIEW.md`
- `docs/reviews/PHASE_11.1.6.2.3_GIT_FINALIZATION_REVIEW.md`
- `docs/migration/LEGACY_API_DECOMMISSION_EXECUTION_RUNBOOK.md`
- `docs/migration/LEGACY_API_DECOMMISSION_ROLLBACK.md`

## Approval Package

Approval directory:

```text
docs/migration/phase11_1_6_execution/approvals/
```

Files:

- `TECHNICAL_APPROVAL.md`
- `BUSINESS_APPROVAL.md`
- `ROLLBACK_OWNER.md`
- `MAINTENANCE_WINDOW.md`
- `MONITORING_OWNER.md`

## Validation

Validator:

```powershell
python scripts\phase11_1_6_3_approval_validator.py
```

Possible outputs:

```text
APPROVAL_COMPLETE
APPROVAL_PENDING
```

## Testing

Run:

```powershell
python scripts\phase11_1_6_3_approval_validator.py
pytest tests\test_phase11_1_6_3_approval_package.py
pytest
powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1
```

Expected without signed approvals:

```text
APPROVAL_PENDING
```

Expected with complete approvals:

```text
APPROVAL_COMPLETE
```

## Git

Branch:

```text
migration/phase-11.1.6.3-approval-package
```

Commit:

```text
docs: add legacy api shutdown approval package
```

Tag:

```text
phase-11.1.6.3-approval-package-ready
```

## Final Status

`WAITING_FOR_APPROVAL_SIGNATURES`

Do not execute shutdown and do not start Phase 11.2.
