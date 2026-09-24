# Phase 11.2 - Legacy Database Archive

## Status

PLANNED

## Objective

Archive the final legacy SQLite database safely after Django owns data.

## Dependencies

- Phase 10.4 approved
- Production data validated in Django database
- Retention policy approved

## Scope

- final backup
- archive database
- retention policy
- restore verification

## DO NOT

- Do not delete the legacy database without verified archive.
- Do not store archive without checksum.

## Implementation Tasks

- Create final SQLite backup.
- Generate checksum and metadata.
- Store archive in approved location.
- Verify restore procedure.
- Document retention and access policy.

## Testing Requirements

- Restore archive to isolated environment.
- Verify row counts.
- Verify checksum.

## Security Requirements

- Restrict archive access.
- Encrypt archive if required.
- Protect auth/session/token data.

## Database Impact

Legacy database becomes archived source-of-record for historical fallback only.

## Rollback Strategy

Restore from verified archive if historical data is required.

## Git Requirements

- Create phase branch.
- Commit archive documentation only.
- Tag phase completion.

## Review Package Requirements

- `docs/reviews/PHASE_11.2_CHANGESET.patch`
- `docs/reviews/PHASE_11.2_REVIEW_SUMMARY.md`

## Completion Criteria

- Archive exists.
- Restore test passes.
- Retention policy is approved.
