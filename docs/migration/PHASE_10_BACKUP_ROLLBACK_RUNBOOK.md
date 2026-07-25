# Phase 10 Backup And Rollback Runbook

## Backup Rule

Before every dry run or cutover attempt:

1. Copy legacy SQLite database.
2. Record file size.
3. Record checksum.
4. Record row counts.
5. Store backup outside the working tree or in approved secure storage.

## Rollback Rule

Rollback must be possible before any production cutover:

1. Stop Django write traffic.
2. Route API/application traffic back to legacy.
3. Restore the verified SQLite backup if needed.
4. Run health endpoint checks.
5. Run API contract smoke tests.
6. Document cause and next corrective phase.

## Rollback Not Tested Yet

This runbook is prepared, but full production rollback rehearsal is not executed
in this phase because no production PostgreSQL ownership migration was run.

## Required Before Phase 10.4

- Restore test from backup.
- Rollback routing test.
- API contract comparison before and after rollback.
- Sign-off from architecture reviewer.
