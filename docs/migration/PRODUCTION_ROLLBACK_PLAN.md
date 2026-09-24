# Production Rollback Plan

## Phase

Phase 10.4 - Production Database Cutover Readiness

## Rollback Objective

Restore service to the legacy database path if production cutover validation
fails.

## Rollback Owner

The rollback owner must be assigned before cutover:

```text
PHASE10_ROLLBACK_OWNER
```

## Rollback Steps

1. Keep Django writes disabled.
2. Stop production traffic switch.
3. Route application/API traffic back to legacy service.
4. Restore verified SQLite backup if the legacy source was modified.
5. Re-run health checks.
6. Re-run API contract smoke tests.
7. Confirm admin login/session behavior.
8. Document failure reason and corrective phase.

## Rollback Verification

| Check | Required |
|---|---|
| Legacy backup exists | Yes |
| Backup checksum matches | Yes |
| Rollback owner online | Yes |
| Traffic route-back plan ready | Yes |
| API smoke test command ready | Yes |
| Auth/session validation ready | Yes |

## Rollback Window

Rollback window must stay open until:

- post-cutover monitoring is clean,
- application writes are validated,
- API contracts are stable,
- rollback owner signs off.

## Current Status

```text
ROLLBACK PLAN DOCUMENTED
PRODUCTION ROLLBACK NOT EXECUTED
```
