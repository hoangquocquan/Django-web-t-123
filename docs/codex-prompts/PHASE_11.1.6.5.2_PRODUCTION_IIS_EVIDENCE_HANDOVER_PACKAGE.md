# Phase 11.1.6.5.2 - Production IIS Evidence Handover Package

## Objective

Create a complete handover package for Windows Server IIS administrators to
collect and deliver production traffic evidence.

## Important Rules

Do not:

- shutdown Legacy API
- disable IIS routes
- modify IIS configuration
- modify proxy
- modify database
- change production code

Only:

- document collection steps
- prepare handover checklist
- validate received evidence

## Required Documents

- `docs/migration/IIS_PRODUCTION_EVIDENCE_COLLECTION_CHECKLIST.md`
- `docs/migration/IIS_PRODUCTION_EVIDENCE_OPERATOR_RUNBOOK.md`
- `docs/reviews/PHASE_11.1.6.5.1_COLLECTION_RESULT.md`
- `docs/migration/IIS_PRODUCTION_EVIDENCE_DEPLOYMENT_GUIDE.md`

## Implementation Tasks

1. Create IIS administrator handover guide.
2. Create evidence delivery checklist.
3. Create evidence package structure guide.
4. Create collection metadata template.
5. Create evidence acceptance validator.
6. Create tests.

## Testing Requirements

Run:

- `python scripts/phase11_1_6_5_2_evidence_acceptance_validator.py`
- `pytest tests/test_phase11_1_6_5_2_evidence_handover.py`
- `pytest`
- `powershell -ExecutionPolicy Bypass -File scripts/run_migration_test.ps1`

Expected:

- Without IIS logs: `EVIDENCE_REJECTED`
- With valid IIS evidence: `EVIDENCE_ACCEPTED`

## Git Requirements

Branch:

`migration/phase-11.1.6.5.2-iis-evidence-handover`

Commit:

`docs: add production IIS evidence handover package`

Tag:

`phase-11.1.6.5.2-evidence-handover-ready`

## Final Status

`WAITING_FOR_REAL_IIS_EVIDENCE_UPLOAD`

Stop. Do not execute shutdown. Do not start Phase 11.2.
