# Phase 14.0 Django Migration Audit Report

## Django Status

```text
DJANGO_PRESENT_BUT_NOT_FULL_OWNER
```

Django has a real backend structure with settings, DRF, apps, URLs, views, serializers, repositories, services, tests, and unmanaged ORM models.

## Legacy Status

```text
LEGACY_STILL_PRESENT
```

The legacy `backend/` remains in the project with custom app server, controllers, services, repositories, middleware, auth, cache, uploads, schema files, and SQLite database.

## Database Status

```text
DATABASE_PARTIALLY_MIGRATED_READ_ONLY
```

Django maps 27 legacy tables as unmanaged read-only models. The legacy SQLite database still has 39 tables. Django business migrations do not exist, and built-in migrations are not applied in the inspected local environment.

## API Status

```text
API_PARTIALLY_MIGRATED
```

Django REST Framework routes exist under `/api/v1/`, but many endpoints are read-only or replacement intent endpoints. Full database-backed write migration and full Django auth ownership are not complete.

## Test Status

Commands executed:

```text
python manage.py check
python manage.py showmigrations
pytest
python scripts/phase_validator.py --phase 13.8
```

Results:

```text
python manage.py check: PASS
python manage.py showmigrations: PASS, built-in migrations listed and unchecked
pytest: PASS, 180 passed
phase_validator 13.8: PASS
ai-factory phase 14.0: BLOCKED safely because Phase 14.0 is not configured in source validator
AI review engine for phase 14.0: PASS with WARNING decision
```

## Evidence

```text
ai-factory/evidence/django_migration_audit.json
```

AI Factory generated its standard evidence package at:

```text
ai-factory/evidence/package.json
```

The current AI review engine writes to:

```text
docs/reviews/PHASE_AI_REVIEW_REPORT.md
```

Note: the task expected `docs/reviews/AI_PHASE_REVIEW_REPORT.md`, but the current AI review implementation uses the existing path above. This audit did not change source code to rename or duplicate that output.

## Known Issues

- Phase 14.0 is not configured in `scripts/phase_validator.py`.
- Because this audit forbids source code changes, the validator was not modified to add Phase 14.0 requirements.
- `python ai-factory/run_ai_factory.py --phase 14.0` was blocked until Phase 14.0 is added to the validator in a future code-change phase.
- `docs.zip` remains untracked and is outside this audit.

## Remaining Work

1. Decide whether Django should own the database schema.
2. Create managed Django models and migrations for approved domains.
3. Replace in-memory write-intent endpoints with durable Django-owned writes.
4. Complete auth/session ownership migration or explicitly retain legacy auth as a dependency.
5. Map or intentionally retire currently unmapped legacy tables.
6. Define a final legacy shutdown plan only after real production traffic evidence and human approval.

## Final Decision

```text
PARTIALLY_MIGRATED
```

The project is not fully migrated to Django. Django is running together with legacy components.
