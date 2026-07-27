# Monitoring Strategy

## Objectives

The monitoring foundation must make the Django migration observable before any
production optimization or public cutover. The first goal is visibility, not
automation-heavy infrastructure.

Primary objectives:

- Confirm the application is reachable.
- Confirm core API endpoints respond successfully.
- Confirm the legacy SQLite database can be read safely.
- Track latency, error rate, traffic volume, and database query timing.
- Provide an alerting model for operators before production deployment.

## Architecture

Recommended monitoring architecture:

1. Application emits structured logs and health-check results.
2. Metrics are collected from Django, the web server, database, and host.
3. Dashboards visualize service health, latency, errors, and database status.
4. Alerts notify operators when thresholds are crossed.
5. Review reports keep migration decisions traceable in Git.

Suggested future tools:

- Prometheus or CloudWatch for metrics.
- Grafana or CloudWatch Dashboards for visualization.
- Sentry or OpenTelemetry collector for error tracing.
- Central log storage such as CloudWatch Logs, ELK, or Loki.

## Metrics

Required service metrics:

- Request count by endpoint and method.
- Response latency: average, p95, p99.
- HTTP error rate: 4xx and 5xx.
- Database query latency.
- Health-check status.
- Memory and CPU usage.

## Logs

Logs should be structured, searchable, and safe for operations review.

Minimum fields:

- timestamp
- level
- logger
- request_id
- method
- path
- status_code
- latency_ms
- client_ip
- user_id when available
- error_code when available

Sensitive fields such as passwords, tokens, reset links, customer drawings, and
personal contact data must never be written into application logs.

## Alerts

Alerts should start conservative to avoid noisy operations.

Critical alerts:

- API unavailable.
- Database unavailable.
- Error rate above threshold.
- p95 latency above threshold for sustained time.

Warning alerts:

- CPU or memory pressure.
- Slow database queries.
- Disk usage growth.
- Missing health-check data.

## Escalation Process

1. Operator receives alert.
2. Operator checks dashboard and latest health-check report.
3. Operator checks centralized logs by request ID or endpoint.
4. Operator follows rollback or mitigation runbook if production impact is confirmed.
5. Incident summary is recorded in docs/reviews or the production incident system.

## Current Phase Boundary

Phase 12.3 creates the monitoring foundation only. It does not deploy Prometheus,
Grafana, Sentry, CloudWatch, IIS changes, Nginx changes, or production agents.

