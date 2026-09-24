# Dashboard Design

## Overview Dashboard

Purpose: one screen for operators to answer "Is the system healthy?"

Panels:

- Overall health status.
- API uptime.
- Request count by status.
- p95 and p99 latency.
- Error rate.
- Database health.
- Recent critical alerts.

## API Dashboard

Purpose: understand endpoint behavior and regressions.

Panels:

- Requests by endpoint.
- Average latency by endpoint.
- p95 latency by endpoint.
- 4xx and 5xx responses.
- Top slow endpoints.
- Legacy `/api/*` vs Django `/api/v1/*` traffic split.

## Database Dashboard

Purpose: understand database safety and query performance.

Panels:

- Database connectivity.
- Query latency.
- Slow query count.
- Connection count.
- Integrity check result while SQLite remains active.
- Database size and disk usage.

## Security Dashboard

Purpose: detect suspicious access and auth problems.

Panels:

- Failed login attempts.
- Permission denied responses.
- Admin actions.
- Sensitive endpoint access.
- Suspicious IP trend.
- Security alert history.

## Phase 12.3 Boundary

This document defines dashboard design only. It does not deploy a dashboard
server or connect production telemetry.

