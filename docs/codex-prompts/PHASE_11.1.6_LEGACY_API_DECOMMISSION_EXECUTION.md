# Phase 11.1.6 - Legacy API Decommission Execution

## Project

mecprecision-vietnam

## Objective

Execute Legacy API decommission safely.

Target:

- Legacy API: `/api/*`
- Replacement API: `/api/v1/*`

## Critical Safety Rules

Before any shutdown action, validate:

- Production evidence: `COMPLETE_EVIDENCE_PACKAGE`
- Technical approval exists
- Business approval exists
- Rollback owner exists
- Maintenance window exists
- Monitoring is ready

If any validation fails:

```text
BLOCKED_SAFELY
```

Do not:

- Delete legacy code.
- Delete database.
- Archive database.
- Remove migrations.
- Modify unrelated APIs.
- Bypass approval gate.

## Required Documents

Read before implementation:

- `docs/migration/LEGACY_API_FINAL_SHUTDOWN_DECISION.md`
- `docs/migration/LEGACY_API_DECOMMISSION_EXECUTION_PLAN.md`
- `docs/migration/LEGACY_API_DECOMMISSION_ROLLBACK.md`
- `docs/migration/production_evidence/`
- `docs/migration/IIS_PRODUCTION_EVIDENCE_DEPLOYMENT_GUIDE.md`
- `docs/reviews/PHASE_11.1.5.5_GIT_FINALIZATION_REVIEW.md`

## Implementation Tasks

1. Create `scripts/phase11_1_6_pre_shutdown_validation.py`.
2. Create `scripts/phase11_1_6_execute_legacy_api_decommission.py`.
3. Create `scripts/phase11_1_6_rollback_legacy_api.py`.
4. Create `docs/migration/LEGACY_API_DECOMMISSION_EXECUTION_RUNBOOK.md`.
5. Create `docs/migration/LEGACY_API_POST_SHUTDOWN_MONITORING.md`.
6. Create `tests/test_phase11_1_6_legacy_api_decommission.py`.
7. Create review package:
   - `docs/reviews/PHASE_11.1.6_REVIEW_SUMMARY.md`
   - `docs/reviews/PHASE_11.1.6_CHANGESET.patch`

## Testing Requirements

Run:

```powershell
python scripts\phase11_1_6_pre_shutdown_validation.py
cd django_backend
python manage.py check
cd ..
pytest tests/test_phase11_1_6_legacy_api_decommission.py
pytest
powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1
```

Expected local result without production approval:

```text
BLOCKED_SAFELY
```

## Git Requirements

Branch:

```text
migration/phase-11.1.6-legacy-api-decommission-execution
```

Commit:

```text
feat: prepare legacy api decommission execution
```

Tag:

```text
phase-11.1.6-ready-for-execution
```

## Final Status

`WAITING_FOR_ARCHITECT REVIEW`

Stop after Phase 11.1.6. Do not start Phase 11.2.
