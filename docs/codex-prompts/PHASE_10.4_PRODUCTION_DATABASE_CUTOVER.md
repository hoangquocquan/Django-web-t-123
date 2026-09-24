# Phase 10.4 - Production Database Cutover

## Status

PLANNED

## Objective

Transfer database ownership to Django production safely.

## Dependencies

- Phase 10.3 reconciliation approved
- Production backup/restore verified
- Maintenance window approved
- Rollback owner assigned

## Scope

- backup
- final sync
- maintenance window
- migration execution
- validation
- rollback readiness

## DO NOT

- Do not cutover without rollback.
- Do not skip final backup.
- Do not enable writes before validation gates pass.

## Implementation Tasks

- Create final backup.
- Freeze legacy writes if required.
- Execute final migration.
- Validate row counts and API responses.
- Switch production database configuration.
- Monitor post-cutover metrics.

## Testing Requirements

- `python manage.py check`
- `pytest`
- smoke tests
- API contract tests
- rollback readiness check

## Security Requirements

- Use production secret handling.
- Verify auth/session behavior before exposing admin flows.

## Database Impact

High. Production ownership changes after approval.

## Rollback Strategy

Restore legacy backup and route traffic back to legacy if validation fails.

## Git Requirements

- Create phase branch.
- Commit cutover docs/config only after approval.
- Tag phase completion.

## Review Package Requirements

- `docs/reviews/PHASE_10.4_CHANGESET.patch`
- `docs/reviews/PHASE_10.4_REVIEW_SUMMARY.md`

## Completion Criteria

- Production validation passes.
- Monitoring is clean.
- Rollback window closes with approval.
