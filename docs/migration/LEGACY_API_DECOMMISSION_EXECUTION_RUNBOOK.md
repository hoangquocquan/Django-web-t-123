# Legacy API Decommission Execution Runbook

## Purpose

This runbook explains how to execute Phase 11.1.6 safely. The target is to stop
serving legacy `/api/*` traffic only after production evidence and approvals are
complete. Replacement Django APIs under `/api/v1/*` must remain active.

## Safety Position

Current repository evidence is not enough to shut down the legacy API in this
local environment.

Expected local validation result:

```text
BLOCKED_SAFELY
```

No script in this phase deletes legacy code, changes the database, edits IIS,
changes proxy rules or modifies Django URL routing.

## Pre-Check

Run:

```powershell
python scripts\phase11_1_6_pre_shutdown_validation.py
```

Required result before production execution:

```text
READY_TO_EXECUTE
```

The validator checks:

- Production evidence status is `COMPLETE_EVIDENCE_PACKAGE`.
- Legacy `/api/*` traffic is zero.
- Django `/api/v1/*` traffic is observed.
- Unknown clients are zero.
- Technical approval exists.
- Business approval exists.
- Rollback owner exists.
- Maintenance window exists.
- Monitoring is ready.

If any check fails, stop:

```text
BLOCKED_SAFELY
```

## Approval Verification

Approval records are read from:

```text
docs/migration/production_evidence/approvals/TECHNICAL_APPROVAL.md
docs/migration/production_evidence/approvals/BUSINESS_APPROVAL.md
docs/migration/production_evidence/approvals/ROLLBACK_OWNER.md
docs/migration/production_evidence/approvals/MAINTENANCE_WINDOW.md
docs/migration/production_evidence/monitoring/MONITORING_READINESS_CONFIRMATION.md
```

For local or CI validation, environment variables can override the documents:

```powershell
$env:PHASE11_1_6_TECHNICAL_APPROVAL="approved"
$env:PHASE11_1_6_BUSINESS_APPROVAL="approved"
$env:PHASE11_1_6_ROLLBACK_OWNER="ops-owner"
$env:PHASE11_1_6_MAINTENANCE_WINDOW="approved"
$env:PHASE11_1_6_MONITORING_READY="approved"
```

These overrides are for validation only. Production execution still requires
real approval records.

## Execution Steps

1. Confirm the maintenance window is active.
2. Confirm rollback owner and monitoring owner are available.
3. Run:

```powershell
python scripts\phase11_1_6_execute_legacy_api_decommission.py
```

4. If the result is `BLOCKED_SAFELY`, do not change routing.
5. If the result is `READY_TO_EXECUTE`, the production operator may apply the
   approved route/proxy change for `/api/*`.
6. Keep `/api/v1/*` active.
7. Write the execution record into:

```text
docs/migration/phase11_1_6_execution/LEGACY_API_DECOMMISSION_EXECUTION_RECORD.json
```

## Validation Steps

After production route changes are applied by the operator, verify:

- `/api/*` is unavailable.
- `/api/v1/*` is available.
- Error rate is not increasing.
- Contact and quotation workflows still work.
- No important client is failing.

Local route validation is represented by the helper function
`verify_post_shutdown_state()` in:

```text
scripts/phase11_1_6_execute_legacy_api_decommission.py
```

## Monitoring

Track during and after the maintenance window:

- Legacy `/api/*` request attempts.
- Replacement `/api/v1/*` traffic.
- 4xx and 5xx error rate.
- API latency.
- Unknown clients.
- Customer impact.

Record findings in:

```text
docs/migration/LEGACY_API_POST_SHUTDOWN_MONITORING.md
```

## Rollback

Run:

```powershell
python scripts\phase11_1_6_rollback_legacy_api.py
```

Rollback operator actions:

1. Restore the previous router/proxy rule for `/api/*`.
2. Keep `/api/v1/*` online.
3. Run smoke tests.
4. Monitor traffic and errors.
5. Record the rollback report.

Rollback report:

```text
docs/migration/phase11_1_6_execution/LEGACY_API_DECOMMISSION_ROLLBACK_REPORT.json
```

## Stop Conditions

Stop or roll back if:

- A known client reports production API failure.
- Unknown legacy clients appear.
- Error rate increases.
- `/api/v1/*` smoke tests fail.
- Monitoring becomes unavailable.
- Rollback owner cannot be reached.

## Current Status

```text
WAITING_FOR_ARCHITECT REVIEW
```

Phase 11.2 has not been started.
