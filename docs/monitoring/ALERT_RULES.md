# Alert Rules

## Critical Alerts

| Alert | Condition | Action |
| --- | --- | --- |
| API unavailable | Health check fails for 2 consecutive checks. | Notify operator immediately and check deployment/runtime status. |
| Database unavailable | Database connectivity or integrity check fails. | Stop risky operations and check database path, permissions, and backup state. |
| High error rate | 5xx error rate above 5 percent for 5 minutes. | Check recent deploys, logs, and API dependency status. |
| High latency | p95 latency above agreed SLA for 10 minutes. | Check database queries, CPU, memory, and upstream dependencies. |

## Warning Alerts

| Alert | Condition | Action |
| --- | --- | --- |
| CPU pressure | CPU above 80 percent for 10 minutes. | Review traffic, jobs, and process usage. |
| Memory pressure | Memory above 85 percent for 10 minutes. | Check leaks, worker count, and cache growth. |
| Disk usage | Disk above 80 percent. | Rotate logs and verify backup/archive growth. |
| Slow queries | Slow query count increasing over baseline. | Inspect query plan and indexes. |
| Missing metrics | No metrics received for 5 minutes. | Check monitoring agent or log pipeline. |

## Migration-Specific Alerts

| Alert | Condition | Action |
| --- | --- | --- |
| Legacy API traffic detected after cutoff | Any `/api/*` legacy request after approved cutoff. | Block shutdown and identify client. |
| Django API error spike | `/api/v1/*` 5xx increase after cutover. | Trigger rollback review. |
| Production evidence missing | Required IIS/API logs not collected. | Keep shutdown blocked safely. |

## Escalation

1. Critical alert: operator review within 15 minutes.
2. Confirmed outage: notify technical owner and business owner.
3. Data integrity risk: freeze write operations until reviewed.
4. Security incident: follow security escalation and preserve logs.

