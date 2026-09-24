# API Monitoring Plan

## Request Logging

Production API logging should capture:

- request path
- HTTP method
- response status
- duration
- user/admin ID after auth cutover
- request ID/correlation ID

Do not log passwords, tokens, session IDs or uploaded file contents.

## Error Tracking

Track:

- 400 invalid request spikes
- 403 permission rejections
- 404 not found spikes
- 500 exceptions
- legacy database connection failures

## Health Monitoring

Monitor:

- `GET /api/health`
- `GET /api/v1/health`
- Django process availability
- legacy SQLite file availability

## Metrics

Required metrics before production traffic:

- request count by endpoint
- p50/p95/p99 latency
- error rate by endpoint
- database query count/timing
- response payload size

## Alert Requirements

Alert when:

- health endpoint reports degraded state
- error rate exceeds agreed threshold
- p95 latency exceeds agreed threshold
- database read failures occur
- unsafe method attempts spike unexpectedly

## Tooling Boundary

Phase 9.2 documents monitoring requirements only. It does not deploy external
monitoring, tracing or alerting tools.
