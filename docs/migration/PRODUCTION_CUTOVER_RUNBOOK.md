# Production Database Cutover Runbook

## Phase

Phase 10.4 - Production Database Cutover Readiness

## Status

```text
CUTOVER NOT EXECUTED
```

## Purpose

This runbook defines the human-approved production database ownership transfer
from legacy SQLite to Django/PostgreSQL. It is a readiness document and does not
switch production traffic by itself.

## Required Approvals

| Gate | Environment Flag |
|---|---|
| Maintenance window approved | `PHASE10_MAINTENANCE_WINDOW_APPROVED=approved` |
| Legacy write freeze approved | `PHASE10_LEGACY_WRITE_FREEZE_APPROVED=approved` |
| Rollback plan approved | `PHASE10_ROLLBACK_APPROVED=approved` |
| Final backup verified | `PHASE10_FINAL_BACKUP_VERIFIED=approved` |

## Required Values

| Value | Environment Variable |
|---|---|
| Production PostgreSQL URL | `PHASE10_PRODUCTION_DATABASE_URL` |
| Final legacy backup path | `PHASE10_FINAL_BACKUP_PATH` |
| Final legacy backup checksum | `PHASE10_FINAL_BACKUP_SHA256` |
| Rollback owner | `PHASE10_ROLLBACK_OWNER` |
| Cutover approval ID | `PHASE10_CUTOVER_APPROVAL_ID` |

## Cutover Sequence

1. Announce maintenance window.
2. Freeze legacy writes.
3. Create final SQLite backup.
4. Record backup file size and SHA256 checksum.
5. Verify rollback owner is online.
6. Run final migration against production PostgreSQL.
7. Validate row counts.
8. Validate API smoke tests and API contract tests.
9. Switch Django production database configuration.
10. Keep writes disabled until validation passes.
11. Enable writes only after validation gates pass.
12. Monitor post-cutover metrics.

## Validation Gates

- `python manage.py check`
- `pytest`
- API health check
- API contract smoke tests
- login/session smoke test
- row-count validation
- rollback readiness check

## Stop Conditions

Stop cutover immediately if:

- final backup is missing,
- backup checksum does not match,
- rollback owner is unavailable,
- API contract test fails,
- row count mismatch is unresolved,
- authentication/session behavior is uncertain,
- production database URL points to test/dry-run/staging/dev database.

## Security Rules

- Never commit production secrets.
- Never print raw database passwords.
- Never expose session IDs, password hashes, reset tokens or 2FA codes.
- Use approved secret manager for production values.

## Current Phase Decision

This phase creates readiness gates and documentation only. Actual production
cutover remains blocked until all approvals and production secrets are provided
through the approved deployment process.
