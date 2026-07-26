# Phase 11.1.6.5.1 - Production IIS Log Collection Execution

## Objective

Create an operational procedure for collecting real IIS production logs from
Windows Server and generating a traffic evidence package.

## Important Rules

Do not:

- shutdown Legacy API
- disable `/api` routes
- modify IIS configuration
- modify proxy
- modify database
- change production code

Only:

- collect logs
- export evidence
- validate traffic

## Required Documents

- `docs/reviews/PHASE_11.1.6.5_PRODUCTION_EVIDENCE_REVIEW.md`
- `docs/migration/IIS_PRODUCTION_EVIDENCE_COLLECTION_CHECKLIST.md`
- `docs/migration/IIS_PRODUCTION_EVIDENCE_OPERATOR_RUNBOOK.md`
- `docs/migration/IIS_PRODUCTION_EVIDENCE_DEPLOYMENT_GUIDE.md`

## Implementation Tasks

1. Create production IIS log collection execution guide.
2. Create IIS collection script wrapper.
3. Create collection evidence validator.
4. Create collection result report.
5. Create automated tests.

## Testing Requirements

Run:

- `python scripts/phase11_1_6_5_1_collection_validator.py`
- `pytest tests/test_phase11_1_6_5_1_iis_collection_execution.py`
- `pytest`
- `powershell -ExecutionPolicy Bypass -File scripts/run_migration_test.ps1`

Expected:

- Without IIS logs: `INCOMPLETE_EVIDENCE_PACKAGE`
- With real IIS logs: `COMPLETE_EVIDENCE_PACKAGE`

## Git Requirements

Branch:

`migration/phase-11.1.6.5.1-iis-log-collection`

Commit:

`feat: add production IIS log collection execution workflow`

Tag:

`phase-11.1.6.5.1-iis-log-collection-ready`

## Final Status

`WAITING_FOR_REAL_IIS_LOG_UPLOAD`

Stop. Do not execute shutdown. Do not start Phase 11.2.
