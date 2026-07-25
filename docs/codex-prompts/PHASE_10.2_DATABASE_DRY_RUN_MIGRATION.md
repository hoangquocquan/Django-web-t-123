# Phase 10.2 - Database Dry Run Migration

## Status

PLANNED

## Objective

Perform migration simulation only.

## Dependencies

- Phase 10.1 PostgreSQL schema design approved
- PostgreSQL test environment available
- Backup and restore procedure documented

## Scope

- test PostgreSQL environment
- generated Django migrations
- sample/full copied data migration
- validation
- rollback simulation

## DO NOT

- Do not touch production database.
- Do not route production traffic.
- Do not remove legacy SQLite.

## Implementation Tasks

- Create PostgreSQL test environment.
- Generate Django migrations from approved schema.
- Migrate sample data or full copied dataset.
- Validate relationships.
- Measure migration time.
- Test rollback.
- Create required outputs:
  - `DATABASE_DRY_RUN_REPORT.md`
  - `MIGRATION_ERROR_REPORT.md`
  - `ROLLBACK_TEST_REPORT.md`

## Testing Requirements

- `python manage.py check`
- `pytest`
- migration command dry-run
- rollback smoke test
- API regression against migrated target

## Security Requirements

- Use non-production secrets.
- Mask sensitive account/token fields in reports.

## Database Impact

Test database only. No production impact.

## Rollback Strategy

Drop test target database and restore from copied backup if dry run fails.

## Git Requirements

- Create phase branch.
- Commit migration scripts/docs only after review.
- Tag phase completion.

## Review Package Requirements

- `docs/reviews/PHASE_10.2_CHANGESET.patch`
- `docs/reviews/PHASE_10.2_REVIEW_SUMMARY.md`

## Completion Criteria

- Dry run completes or failures are documented.
- Rollback test report exists.
- Reviewer approves readiness for reconciliation.
