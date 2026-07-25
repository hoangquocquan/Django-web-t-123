# Phase 11.1 - Legacy API Decommission

## Status

PLANNED

## Objective

Disable old legacy API routes after Django API cutover is fully verified.

## Dependencies

- Phase 10.4 approved
- Django API contracts pass in production
- Traffic logs prove no clients use legacy routes

## Scope

- disable old API
- archive routes
- remove compatibility adapters
- verify traffic migration

## DO NOT

- Do not remove routes without traffic evidence.
- Do not break documented rollback window.

## Implementation Tasks

- Identify legacy API routes.
- Compare with Django replacements.
- Disable or redirect legacy endpoints.
- Archive route documentation.
- Remove compatibility adapters only when safe.

## Testing Requirements

- Django API regression.
- Legacy route traffic smoke check.
- Client contract tests.

## Security Requirements

- Avoid leaking deprecated endpoints publicly.
- Preserve access logs for audit.

## Database Impact

None expected.

## Rollback Strategy

Re-enable legacy routes or proxy mapping if client issues appear.

## Git Requirements

- Create phase branch.
- Commit route/config changes.
- Tag phase completion.

## Review Package Requirements

- `docs/reviews/PHASE_11.1_CHANGESET.patch`
- `docs/reviews/PHASE_11.1_REVIEW_SUMMARY.md`

## Completion Criteria

- Legacy API no longer handles production traffic.
- Django endpoint replacements are verified.
