# Observability runbook

Status: platform wiring and alert tests are `MANUAL_EXECUTION_REQUIRED`. Collect structured stdout logs, protected metrics and traces without secrets or raw customer content. Alert on 5xx, p95 latency, readiness, PostgreSQL locks/connections/storage, Redis errors/latency/memory, worker queues, AI provider failures and media failure. Route severity-1 to on-call, link dashboards to incidents, test alerts in staging and retain delivery evidence.

Checklist: correlation ID present; retention approved; metrics scrape authenticated; dashboard owned; pager route tested; escalation and silence expiry defined; audit-event gaps, RAG refusal/error rate, auth-denial spikes, p95/p99 latency and external-provider failure rate visible.
