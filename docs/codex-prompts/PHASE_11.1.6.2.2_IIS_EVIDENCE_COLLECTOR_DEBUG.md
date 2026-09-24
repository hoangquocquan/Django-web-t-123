# Phase 11.1.6.2.2 - IIS Evidence Collector Debug

## Project

mecprecision-vietnam

## Objective

Debug the IIS evidence collection pipeline so valid IIS W3C logs can be
converted into `iis_api_evidence.csv` with detected `/api/*` and `/api/v1/*`
traffic.

## Current Issue

`iis_api_evidence.csv` currently contains:

```text
records: 0
```

Production traffic cannot be validated from an empty evidence export.

## Important Rules

Do not:

- Modify IIS configuration.
- Restart IIS.
- Change API routes.
- Disable Legacy API.
- Modify production system.

Only:

- Debug parser.
- Improve validation.
- Document issues.

## Required Documents

- `docs/migration/IIS_PRODUCTION_EVIDENCE_DEPLOYMENT_GUIDE.md`
- `docs/reviews/PHASE_11.1.6.2_EVIDENCE_REVIEW.md`
- `docs/migration/production_evidence/`

## Implementation Tasks

1. Analyze current IIS collector.
2. Improve IIS parser safety if required.
3. Create `scripts/windows/diagnose_iis_evidence.ps1`.
4. Create `tests/test_phase11_1_6_2_2_iis_debug.py`.
5. Create `docs/reviews/PHASE_11.1.6.2.2_IIS_DEBUG_ANALYSIS.md`.
6. Create `docs/reviews/PHASE_11.1.6.2.2_IIS_DEBUG_REVIEW.md`.

## Testing Requirements

Run:

```powershell
python scripts\phase11_1_6_2_1_import_iis_production_data.py
python scripts\phase11_1_6_1_final_evidence_validator.py
pytest tests\test_phase11_1_6_2_2_iis_debug.py
pytest
powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1
```

Expected without real IIS logs:

```text
INCOMPLETE_EVIDENCE_PACKAGE
```

Expected with valid IIS logs:

```text
COMPLETE_EVIDENCE_PACKAGE
```

## Git Requirements

Branch:

```text
migration/phase-11.1.6.2.2-iis-debug
```

Commit:

```text
fix: debug IIS production evidence collector
```

Tag:

```text
phase-11.1.6.2.2-iis-debug-complete
```

## Final Status

`WAITING_FOR_ARCHITECT REVIEW`

Do not execute shutdown and do not start Phase 11.2.
