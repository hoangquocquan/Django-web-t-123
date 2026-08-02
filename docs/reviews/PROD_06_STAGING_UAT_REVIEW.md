# PROD-06 Staging UAT Review

## Decision

`PASS` - PROD-06 completed its production-like local staging validation and is
eligible for PROD-07 after the dedicated commit is recorded. Human approval is
still required for any merge or deployment.

## Runtime

| Component | Result | Evidence |
| --- | --- | --- |
| Django/Gunicorn | PASS | Production settings, `DEBUG=False`, healthy non-root container |
| PostgreSQL | PASS | Container/query health and isolated restore migration check |
| Redis | PASS | Container health, cache probe and distributed controls |
| Ollama | PASS | Local endpoint, `llama3` and `nomic-embed-text` available |
| n8n | PASS | Healthy runtime and authenticated live HMAC workflow execution |
| HTTPS equivalent | PASS | Trusted local reverse-proxy header contract |

No production deployment was performed.

## UAT And Tests

- Role, login/logout/expiry/unauthorized behavior: PASS.
- CRM create/update/interaction/note/task/owner/due/completion/timeline: PASS.
- Sales lead/opportunity/quotation/approval/follow-up/handoff: PASS.
- Knowledge upload/security/index/reindex/search/RAG/citation/no-context: PASS.
- AI Sales deterministic scoring, strict output and draft-only behavior: PASS.
- AI Agent read-only tools, permissions, audit, timeout and dangerous-action denial: PASS.
- Governance prompt injection, Unicode, secret/PII and distributed limit controls: PASS.
- n8n HMAC, correlation ID, bounded retry and human gate: PASS.
- Focused UAT: 99 passed.
- Security-focused verification after final harness changes: 16 passed.
- Full regression: 512 passed in 61.27 seconds.
- Django check and `makemigrations --check --dry-run`: PASS.
- Migrations created by PROD-06: none.

## Load Smoke

- Virtual users: 20.
- Requests: 140 read-only requests across dashboard, customer, lead,
  quotation, Knowledge and AI surfaces.
- Errors: 0; error rate 0%.
- p50: 63.46 ms; p95: 696.27 ms; p99: 747.80 ms.
- Threshold: p95 <= 2000 ms and error rate <= 1%.
- Result: PASS; slowest surface in the final run was the dashboard access path.

This bounded smoke is readiness evidence, not a production capacity SLA.

## Recovery

- Fresh checksummed staging backup: PASS.
- Isolated PostgreSQL restore and migration check: PASS.
- Media/n8n runtime/workflow restore: PASS.
- Rollback dry-run: PASS.
- Production data modified: false.

## Security

- Production dependency audit: no known vulnerabilities.
- Scoped Ruff, Mypy and Bandit for PROD-06: PASS; Critical 0, High 0.
- Secret-pattern scan: 0 matches.
- Repository Bandit: High 0, Medium 19 inherited warnings documented in evidence.
- Docker Scout: `BLOCKED_BY_ENVIRONMENT` because execution could transmit local
  image metadata to an external service. It is not reported as PASS.

## Corrected UAT Defect

An unauthenticated CRM compatibility path returned HTTP 500 because the retired
legacy SQLite database is absent from the production image. Production/staging
now fails closed with HTTP 403 before any legacy query. Development/test
compatibility remains intact. The rebuilt image and load smoke passed.

## Mandatory Ollama Review

- Decision: PASS.
- Endpoint reachable: true.
- Model available: true (`llama3`).
- Response received: true.
- Schema valid: true.
- Fallback used: false.
- Critical findings: 0.
- High findings: 0.
- Attempts: 1.
- Gate state: `WAITING_HUMAN_APPROVAL`.

## Safety Gates

```json
{
  "human_approval_required": true,
  "auto_merge": false,
  "auto_deploy": false,
  "approval_bypass_detected": false
}
```

No merge, push, Git tag or production deployment was performed.
