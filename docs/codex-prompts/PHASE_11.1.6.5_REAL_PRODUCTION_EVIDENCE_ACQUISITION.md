# Phase 11.1.6.5 - Real Production Evidence Acquisition

## Objective

Acquire and validate real production traffic evidence from Windows Server IIS.

Target transition:

- From: `INCOMPLETE_EVIDENCE_PACKAGE`
- To: `COMPLETE_EVIDENCE_PACKAGE`

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
- analyze traffic
- generate evidence reports

## Required Documents

- `docs/reviews/PHASE_11.1.6.4_FINAL_READINESS_REPORT.md`
- `docs/migration/IIS_PRODUCTION_EVIDENCE_COLLECTION_CHECKLIST.md`
- `docs/migration/IIS_PRODUCTION_EVIDENCE_OPERATOR_RUNBOOK.md`
- `docs/migration/IIS_PRODUCTION_EVIDENCE_DEPLOYMENT_GUIDE.md`

## Implementation Tasks

1. Create production evidence intake procedure.
2. Create evidence package validator.
3. Create production evidence review report.
4. Create evidence import template CSV.
5. Create tests.

## Testing Requirements

Run:

- `python scripts/phase11_1_6_5_production_evidence_validator.py`
- `pytest tests/test_phase11_1_6_5_production_evidence.py`
- `pytest`
- `powershell -ExecutionPolicy Bypass -File scripts/run_migration_test.ps1`

Expected:

- Without real logs: `INCOMPLETE_EVIDENCE_PACKAGE`
- With IIS production logs: `COMPLETE_EVIDENCE_PACKAGE`

## Git Requirements

Branch:

`migration/phase-11.1.6.5-real-production-evidence`

Commit:

`feat: add real production evidence acquisition workflow`

Tag:

`phase-11.1.6.5-production-evidence-ready`

## Final Status

`WAITING_FOR_REAL_IIS_DATA`

Stop. Do not execute shutdown. Do not start Phase 11.2.
