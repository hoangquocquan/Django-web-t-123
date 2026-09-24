# Metrics Catalog

## Application Metrics

| Metric | Description | Source | Recommended threshold |
| --- | --- | --- | --- |
| request_count | Number of requests by endpoint, method and status. | Django middleware or web server logs | Watch trend by hour and day |
| response_latency_ms | Request duration in milliseconds. | Django middleware or API gateway | p95 below agreed SLA |
| error_rate | Percentage of failed responses. | Django logs or API gateway | Critical above 5 percent for 5 minutes |
| 5xx_count | Server-side error count. | Django logs | Critical if above 0 on core APIs |
| active_sessions | Number of active user sessions. | Django session store | Warning on unusual spikes |
| ai_request_count | Number of AI assistant requests. | AI service logs | Watch cost and capacity |

## System Metrics

| Metric | Description | Source | Recommended threshold |
| --- | --- | --- | --- |
| cpu_usage_percent | Host CPU usage. | OS agent | Warning above 80 percent for 10 minutes |
| memory_usage_percent | Host memory usage. | OS agent | Warning above 85 percent for 10 minutes |
| disk_usage_percent | Disk utilization. | OS agent | Warning above 80 percent, critical above 90 percent |
| network_in_out | Network traffic volume. | OS or cloud metrics | Watch for traffic anomalies |

## Database Metrics

| Metric | Description | Source | Recommended threshold |
| --- | --- | --- | --- |
| query_latency_ms | Time spent executing queries. | Django DB instrumentation or database logs | Investigate p95 above 100 ms |
| slow_query_count | Count of slow queries. | Database logs | Warning when increasing |
| connection_count | Active database connections. | Database metrics | Warning near configured limit |
| integrity_check | SQLite integrity result while legacy database remains in use. | Health check script | Critical when not ok |

## Security Metrics

| Metric | Description | Source | Recommended threshold |
| --- | --- | --- | --- |
| failed_login_count | Failed login attempts. | Auth logs | Warning on repeated attempts |
| permission_denied_count | Authorization failures. | API logs | Watch for spikes |
| suspicious_ip_count | Requests from blocked or unusual IPs. | WAF/proxy logs | Escalate if repeated |

## Migration Metrics

| Metric | Description | Source | Recommended threshold |
| --- | --- | --- | --- |
| legacy_api_request_count | Requests still using legacy `/api/*`. | IIS/Nginx/API logs | Must be zero before shutdown |
| django_api_request_count | Requests using `/api/v1/*`. | Django/API logs | Should trend upward after cutover |
| rollback_readiness | Whether rollback artifacts are current. | Review package | Must be ready before production change |

