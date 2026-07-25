# Phase 10.1 - PostgreSQL Schema Design

## Status

PLANNED

## Objective

Design target PostgreSQL schema before migration.

## Dependencies

- Phase 9.3 readiness validation
- `docs/migration/UNMANAGED_MODEL_INVENTORY.md`
- `docs/migration/DATABASE_DEPENDENCY_INVENTORY.md`

## Scope

- review 27 legacy models
- design Django managed models
- define primary keys
- define foreign keys
- define indexes
- define constraints
- resolve composite key strategy
- define naming convention

## DO NOT

- Do not migrate data.
- Do not change production database.
- Do not run production migrations.

## Implementation Tasks

- Review every legacy unmanaged model.
- Propose managed Django model structure.
- Define PostgreSQL field types.
- Define unique constraints and indexes.
- Decide composite key handling.
- Create required documents:
  - `docs/migration/POSTGRESQL_SCHEMA_DESIGN.md`
  - `docs/migration/COMPOSITE_KEY_STRATEGY.md`
  - `docs/migration/SCHEMA_MIGRATION_DECISION_RECORD.md`

## Testing Requirements

- Documentation consistency review.
- Model field mapping review.
- Constraint/index checklist.

## Security Requirements

- Treat account/session/token tables as high-risk.
- Do not expose password hashes or tokens in docs examples.

## Database Impact

None. Design only.

## Rollback Strategy

Not applicable for runtime; revise schema design through a minor phase if
review finds issues.

## Git Requirements

- Create phase branch.
- Commit documentation only.
- Tag phase completion.

## Review Package Requirements

- `docs/reviews/PHASE_10.1_CHANGESET.patch`
- `docs/reviews/PHASE_10.1_REVIEW_SUMMARY.md`

## Completion Criteria

- Target schema design is complete.
- Composite key strategy is decided.
- Architecture reviewer approves schema design.
