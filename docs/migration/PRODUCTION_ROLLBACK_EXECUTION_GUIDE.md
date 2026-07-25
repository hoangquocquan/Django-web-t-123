# Production Rollback Execution Guide

## Phase

Phase 10.5 - Production Cutover Execution & Validation

## Rollback Triggers

- migration failure
- data inconsistency
- API failure
- authentication failure
- monitoring error spike
- operator stop decision

## Rollback Steps

1. Stop traffic to Django PostgreSQL owner path.
2. Keep writes disabled.
3. Restore database from verified backup.
4. Revert production database configuration.
5. Route traffic back to legacy service.
6. Validate system health.
7. Run API contract smoke tests.
8. Run authentication/session smoke tests.
9. Keep monitoring enabled.
10. Record incident and corrective phase.

## Required Rollback Evidence

| Evidence | Required |
|---|---|
| Rollback owner | Yes |
| Backup path | Yes |
| Backup checksum | Yes |
| Restore command reviewed | Yes |
| Traffic route-back command reviewed | Yes |
| API smoke result | Yes |
| Auth smoke result | Yes |

## Current Status

```text
ROLLBACK GUIDE PREPARED
ROLLBACK NOT EXECUTED
```
