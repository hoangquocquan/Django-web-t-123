# Phase 10 - Database Ownership Migration

## Status

PLANNED

## Objective

Move Django from legacy database reader to database owner.

## Dependencies

- Phase 9.3 approved
- Database dependency inventory reviewed
- PostgreSQL schema design approved
- Backup and rollback strategy approved

## Scope

- PostgreSQL transition
- schema ownership
- Django migrations
- data migration
- validation

## DO NOT

- Do not migrate production directly.
- Do not remove backup.
- Do not skip rollback.
- Do not change legacy database until dry runs pass.

## Implementation Tasks

- Confirm target database environment.
- Convert approved unmanaged model designs into managed Django models.
- Create Django migrations in a controlled branch.
- Build data migration scripts.
- Validate row counts and relationships.
- Prepare cutover and rollback runbooks.

## Testing Requirements

- `python manage.py check`
- `pytest`
- migration dry-run tests
- row-count validation
- relationship validation
- rollback simulation

## Security Requirements

- Protect credentials and secrets.
- Do not expose auth/session/token data.
- Review accounts migration separately before enabling writes.

## Database Impact

High. This phase changes ownership from legacy SQLite to Django-managed database
after approval.

## Rollback Strategy

Keep legacy SQLite backup and route traffic back to legacy if validation fails.

## Git Requirements

- Create phase branch.
- Create checkpoint commit.
- Commit final work with `feat:` or `refactor:` prefix.
- Create phase tag.

## Review Package Requirements

- `docs/reviews/PHASE_10_CHANGESET.patch`
- `docs/reviews/PHASE_10_REVIEW_SUMMARY.md`

## Completion Criteria

- Data ownership migration plan executed in approved environment.
- All validation reports pass.
- Rollback plan tested.
- Architecture reviewer approves Phase 10 result.
