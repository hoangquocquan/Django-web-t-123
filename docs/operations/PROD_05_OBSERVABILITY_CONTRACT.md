# PROD-05 Observability Contract

## Endpoints

- `GET /api/v1/metrics/`: Prometheus text, protected by `METRICS_BEARER_TOKEN`.
- `GET /api/v1/operations/health/`: sanitized dependency snapshot using the same token.
- `GET /api/v1/health/`: public load-balancer health contract; it does not expose dependency detail.

The metrics token is stored in the environment secret store and mounted into Prometheus as a file. It must never be placed in Git or dashboard JSON.

## Coverage

The runtime exports HTTP count and duration, application errors, PostgreSQL and Redis reachability, disk/CPU/memory, Ollama, n8n, sessions, failed login attempts, AI governance blocks, knowledge uploads/extractions, database connections, and AI agent queue depth.

Routes use Django route templates instead of raw URLs. Logs do not include query strings, bodies, bearer tokens, prompt text, uploaded content, email addresses, or customer drawing data.

## Error Tracking

Unhandled exceptions and 5xx responses are emitted as structured JSON with a correlation ID. The platform log collector is responsible for retention and notification. Error records must be searched by correlation ID and time window.

## Uptime

The external uptime monitor checks `/api/v1/health/` every minute. Prometheus checks dependency metrics every 30 seconds. Two failed uptime checks or a dependency-down state lasting two minutes opens an incident.
