# Phase 13.1 - Architecture Cleanup

## Status

PLANNED

## Objective

Remove temporary architecture created only for migration safety.

## Dependencies

- Phase 13 approved
- Legacy compatibility no longer required

## Scope

- remove temporary adapters
- simplify services
- improve Django structure

## DO NOT

- Do not remove needed domain boundaries.
- Do not combine unrelated modules.
- Do not break API contracts.

## Implementation Tasks

- Inventory temporary compatibility code.
- Decide which services/repositories remain valuable.
- Remove obsolete adapters.
- Update imports and docs.
- Run full regression.

## Testing Requirements

- Full regression tests.
- API contract tests.
- Import/dependency scan.

## Security Requirements

- Preserve permission checks.
- Preserve sensitive-field protections.

## Database Impact

None expected.

## Rollback Strategy

Restore prior architecture from Git tag if cleanup changes behavior.

## Git Requirements

- Create phase branch.
- Commit cleanup with `refactor:` prefix.
- Tag phase completion.

## Review Package Requirements

- `docs/reviews/PHASE_13.1_CHANGESET.patch`
- `docs/reviews/PHASE_13.1_REVIEW_SUMMARY.md`

## Completion Criteria

- Temporary architecture removed safely.
- Docs match current structure.
