# Phase 11 - Legacy System Shutdown

## Status

PLANNED

## Objective

Remove dependency on the legacy system after Django safely owns behavior and
data.

## Dependencies

- Phase 10 production database cutover approved
- No production traffic depends on legacy APIs
- Legacy rollback window closed

## Scope

- legacy service shutdown planning
- dependency removal
- archive strategy
- operational verification

## DO NOT

- Do not shut down legacy before traffic migration is verified.
- Do not delete backups.
- Do not remove code without archive/review.

## Implementation Tasks

- Audit remaining legacy dependencies.
- Create shutdown runbook.
- Confirm zero production traffic.
- Archive required assets.
- Prepare decommission review package.

## Testing Requirements

- API smoke tests against Django.
- Traffic verification.
- Restore verification for archived data.

## Security Requirements

- Preserve audit logs.
- Protect archived credentials and database files.

## Database Impact

No active database migration. Legacy database becomes archive-only.

## Rollback Strategy

Keep legacy runtime and database archive until shutdown approval is final.

## Git Requirements

- Create phase branch.
- Commit docs/config removals only after approval.
- Tag phase completion.

## Review Package Requirements

- `docs/reviews/PHASE_11_CHANGESET.patch`
- `docs/reviews/PHASE_11_REVIEW_SUMMARY.md`

## Completion Criteria

- Legacy system no longer receives traffic.
- Archive and restore are verified.
- Architecture reviewer approves shutdown.
