# Logging Standard

## Purpose

Logs must help operators diagnose incidents without exposing customer or system
secrets. Logging is part of operations, security, and migration evidence.

## Log Levels

| Level | Usage |
| --- | --- |
| DEBUG | Local development only. Never enable broadly in production. |
| INFO | Normal operational events such as startup and completed health checks. |
| WARNING | Recoverable issues that require attention if repeated. |
| ERROR | Failed requests or failed background jobs. |
| CRITICAL | Service outage, database unavailable, or data safety risk. |

## Log Format

Recommended structured JSON fields:

- timestamp
- level
- environment
- service
- correlation_id
- method
- path
- status_code
- latency_ms
- message
- error_code

Application runtime logs deliberately omit client IP and user identity by default.
Security audit tables retain hashed identifiers under their own access and retention
policy.

## Sensitive Data Rules

Never log:

- passwords
- password reset tokens
- session tokens
- API keys
- private customer drawings
- quote attachment contents
- full email message bodies unless explicitly approved for support tooling

Mask:

- emails after the first characters
- phone numbers except the final digits
- IP addresses when exported outside operations

## Retention Policy

Suggested baseline:

- Application logs: 30 days.
- Security logs: 180 days.
- Access logs: 90 days.
- Incident evidence: retained with the incident record.

Retention must follow customer agreements and legal requirements before real
production deployment.

## Troubleshooting Usage

1. Start from the alert.
2. Search logs by endpoint, request ID, or time window.
3. Compare application logs with database and web server logs.
4. Record findings in the incident or review package.
