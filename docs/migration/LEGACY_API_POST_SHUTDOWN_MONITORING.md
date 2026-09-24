# Legacy API Post Shutdown Monitoring

## Purpose

This document records post-shutdown monitoring for Legacy API decommission. It
is prepared in Phase 11.1.6, but it should only be completed after a real
approved production route change.

## Current Execution Status

```text
NOT_EXECUTED
```

Reason:

```text
Production evidence and approvals must pass before shutdown.
```

## Traffic

| Metric | Status | Notes |
|---|---|---|
| Legacy `/api/*` request attempts | PENDING | Requires production monitoring |
| Django `/api/v1/*` requests | PENDING | Requires production monitoring |
| Unknown clients | PENDING | Requires production monitoring |
| Contact workflow requests | PENDING | Requires production monitoring |
| Quote workflow requests | PENDING | Requires production monitoring |

## Errors

| Metric | Status | Notes |
|---|---|---|
| 4xx rate | PENDING | Compare with baseline |
| 5xx rate | PENDING | Compare with baseline |
| API exception count | PENDING | Watch during maintenance window |
| Client failure reports | PENDING | Support team confirmation required |

## Latency

| Metric | Status | Notes |
|---|---|---|
| `/api/v1/*` p50 latency | PENDING | Requires production monitoring |
| `/api/v1/*` p95 latency | PENDING | Requires production monitoring |
| `/api/v1/*` p99 latency | PENDING | Requires production monitoring |

## Customer Impact

| Area | Status | Notes |
|---|---|---|
| Website visitors | PENDING | Monitor frontend API calls |
| CMS users | PENDING | Confirm admin workflows |
| Contact submissions | PENDING | Confirm stored successfully |
| Quote requests | PENDING | Confirm stored successfully |
| External integrations | PENDING | Confirm no legacy dependency |

## Rollback Decision

Current decision:

```text
ROLLBACK_NOT_REQUIRED_BECAUSE_SHUTDOWN_NOT_EXECUTED
```

Rollback must be executed if:

- Important clients receive new 4xx or 5xx errors.
- `/api/v1/*` fails smoke tests.
- Unknown legacy clients appear after shutdown.
- Error rate or latency increases beyond the approved threshold.

## Final Monitoring Sign-Off

| Role | Name | Status |
|---|---|---|
| Technical owner | PENDING | PENDING |
| Business owner | PENDING | PENDING |
| Monitoring owner | PENDING | PENDING |
| Rollback owner | PENDING | PENDING |
