# Phase 11 Operations Master Runbook

## Pre-Check

Before any production action, confirm:

- `FINAL_READINESS_STATUS.json` is not `BLOCKED_SAFELY`.
- final gate returns `READY_TO_EXECUTE_PRODUCTION`.
- evidence is `REAL_PRODUCTION_EVIDENCE`.
- `simulation = false`.
- real approvals are signed.
- rollback owner and monitoring owner are online.

Current repository status:

`BLOCKED_SAFELY`

## Execution Checklist

- [ ] Confirm approved maintenance window.
- [ ] Confirm production evidence package.
- [ ] Confirm technical approval.
- [ ] Confirm business approval.
- [ ] Confirm rollback owner.
- [ ] Confirm monitoring owner.
- [ ] Run pre-shutdown validation.
- [ ] Run final readiness gate in production mode.
- [ ] Only after approval, operator applies route/proxy change.

## Monitoring Checklist

Monitor during and after a future approved shutdown:

- `/api/*` request attempts
- `/api/v1/*` request volume
- unknown clients
- HTTP 4xx/5xx rate
- latency
- contact flow
- quotation flow
- customer incident reports

## Rollback Checklist

- [ ] Stop additional route changes.
- [ ] Restore previous `/api/*` router/proxy rule.
- [ ] Keep `/api/v1/*` online.
- [ ] Run smoke tests.
- [ ] Verify request volume normalizes.
- [ ] Record rollback report.
- [ ] Open corrective minor phase before retry.

## Incident Handling

Rollback immediately if:

- known clients fail,
- unknown legacy clients appear,
- error rates spike,
- `/api/v1/*` fails smoke tests,
- monitoring becomes unavailable,
- rollback owner cannot be reached.

## Current Operational Decision

Training: `READY_TO_EXECUTE_TRAINING`

Production: `BLOCKED_SAFELY`
