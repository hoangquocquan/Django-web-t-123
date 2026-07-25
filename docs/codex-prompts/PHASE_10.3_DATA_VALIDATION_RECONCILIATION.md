# Phase 10.3 - Data Validation Reconciliation

## Status

PLANNED

## Objective

Validate migrated data accuracy.

## Dependencies

- Phase 10.2 dry run completed
- Source and target databases available for comparison

## Scope

- Catalog validation
- CRM validation
- Sales validation
- CMS validation
- Accounts validation

## DO NOT

- Do not mutate production data.
- Do not approve cutover with unresolved mismatches.

## Implementation Tasks

- Compare row counts.
- Validate checksums.
- Validate relationships.
- Detect orphan rows.
- Validate business rules.
- Create `docs/migration/DATA_RECONCILIATION_REPORT.md`.

## Testing Requirements

- Reconciliation script tests.
- API response comparison.
- Full regression tests.

## Security Requirements

- Do not print raw passwords, tokens or session IDs.
- Restrict access to reconciliation artifacts.

## Database Impact

Read-only comparison only.

## Rollback Strategy

If reconciliation fails, return to Phase 10.2 dry run fixes.

## Git Requirements

- Create phase branch.
- Commit validation docs/scripts.
- Tag phase completion.

## Review Package Requirements

- `docs/reviews/PHASE_10.3_CHANGESET.patch`
- `docs/reviews/PHASE_10.3_REVIEW_SUMMARY.md`

## Completion Criteria

- Reconciliation report completed.
- Mismatches resolved or explicitly accepted.
- Reviewer approves production cutover planning.
