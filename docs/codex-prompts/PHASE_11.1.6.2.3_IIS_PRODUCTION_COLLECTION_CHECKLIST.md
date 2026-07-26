# Phase 11.1.6.2.3 - IIS Production Evidence Collection Checklist

## Project

mecprecision-vietnam

## Objective

Create an operational checklist for collecting real IIS production evidence
before Legacy API shutdown.

## Current Status

```text
INCOMPLETE_EVIDENCE_PACKAGE
```

Root cause:

```text
No real IIS production traffic logs available.
```

## Important Rules

Do not:

- Disable Legacy API.
- Modify IIS.
- Change routing.
- Restart production services.
- Execute shutdown.

Only:

- Collect evidence.
- Verify logs.
- Document results.

## Required Documents

- `docs/migration/IIS_PRODUCTION_EVIDENCE_DEPLOYMENT_GUIDE.md`
- `docs/reviews/PHASE_11.1.6.2.2_IIS_DEBUG_REVIEW.md`
- `docs/migration/production_evidence/`

## Implementation Tasks

1. Create `docs/migration/IIS_PRODUCTION_EVIDENCE_COLLECTION_CHECKLIST.md`.
2. Create `docs/migration/IIS_PRODUCTION_EVIDENCE_OPERATOR_RUNBOOK.md`.
3. Document expected evidence package structure.
4. Create `docs/migration/production_evidence/IIS_COLLECTION_RESULT_TEMPLATE.md`.
5. Create `tests/test_phase11_1_6_2_3_collection_checklist.py`.

## Testing Requirements

Run:

```powershell
pytest tests\test_phase11_1_6_2_3_collection_checklist.py
pytest
powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1
```

Expected:

```text
PASS
```

## Git Requirements

Branch:

```text
migration/phase-11.1.6.2.3-iis-collection-checklist
```

Commit:

```text
docs: add IIS production evidence collection checklist
```

Tag:

```text
phase-11.1.6.2.3-iis-collection-ready
```

## Final Status

`WAITING_FOR_PRODUCTION_IIS_EVIDENCE`

Do not execute shutdown and do not start Phase 11.2.
