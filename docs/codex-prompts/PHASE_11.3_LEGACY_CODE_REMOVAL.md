# Phase 11.3 - Legacy Code Removal

## Status

PLANNED

## Objective

Remove unused legacy code after the legacy system is fully decommissioned.

## Dependencies

- Phase 11.1 legacy API decommission approved
- Phase 11.2 database archive approved
- No rollback dependency remains

## Scope

- remove unused legacy code
- remove compatibility layer
- cleanup dependencies
- update documentation

## DO NOT

- Do not remove code still used by production.
- Do not remove archival docs.
- Do not remove rollback references before approval.

## Implementation Tasks

- Identify legacy files no longer used.
- Remove obsolete compatibility adapters.
- Cleanup dependency files.
- Update README and architecture docs.
- Run full test suite.

## Testing Requirements

- `python manage.py check`
- `pytest`
- production smoke test
- import/dependency scan

## Security Requirements

- Ensure removed code does not delete audit/backup artifacts.
- Preserve security docs and incident history.

## Database Impact

None expected.

## Rollback Strategy

Restore removed code from Git tag if unexpected dependency appears.

## Git Requirements

- Create phase branch.
- Commit removals with `refactor:` prefix.
- Tag phase completion.

## Review Package Requirements

- `docs/reviews/PHASE_11.3_CHANGESET.patch`
- `docs/reviews/PHASE_11.3_REVIEW_SUMMARY.md`

## Completion Criteria

- Legacy code removed safely.
- Tests pass.
- Documentation reflects Django-only architecture.
