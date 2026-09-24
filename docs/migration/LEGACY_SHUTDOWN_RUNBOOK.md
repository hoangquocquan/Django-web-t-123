# Legacy Shutdown Runbook

## Purpose

This runbook explains how to shut down the legacy system only after Django has
been verified as the production owner.

## Current Status

```text
NOT APPROVED FOR EXECUTION
```

Do not run shutdown commands while `LEGACY_SHUTDOWN_DECISION_REPORT.md` says
`KEEP_LEGACY_ACTIVE`.

## Required Evidence Before Shutdown

| Evidence | Required marker |
|---|---|
| Traffic migration verified | `PHASE11_TRAFFIC_MIGRATION_VERIFIED=verified` |
| Zero legacy traffic confirmed | `PHASE11_ZERO_LEGACY_TRAFFIC_CONFIRMED=verified` |
| Rollback window closed | `PHASE11_ROLLBACK_WINDOW_CLOSED=completed` |
| Archive restore verified | `PHASE11_ARCHIVE_RESTORE_VERIFIED=verified` |
| Business owner approval | `PHASE11_BUSINESS_OWNER_APPROVED=approved` |
| Architecture approval | `ALLOW_PHASE_11` in decision report |

## Readiness Command

```powershell
python scripts\phase11_legacy_shutdown_readiness.py
```

Use strict mode in CI:

```powershell
python scripts\phase11_legacy_shutdown_readiness.py --strict
```

## Manual Shutdown Sequence After Approval

1. Announce maintenance window.
2. Confirm Django health checks and business smoke tests pass.
3. Confirm production logs show zero requests to legacy routes.
4. Create final archive package for legacy source, database, uploads and logs.
5. Verify archive restore on a separate machine or isolated folder.
6. Stop legacy service.
7. Keep legacy database and code archive read-only.
8. Monitor Django errors, latency, authentication and business flows.
9. Record the shutdown approval ID and operator name.

## Stop Conditions

Stop immediately if any condition below happens:

- Any traffic still reaches legacy.
- Django API smoke tests fail.
- Archive restore cannot be verified.
- Rollback owner does not approve closure.
- Architecture reviewer does not approve shutdown.

## Rollback

Until final shutdown approval is recorded, keep the legacy runtime and database
archive available. If Django production validation fails, route traffic back to
legacy and keep Phase 11 blocked.
