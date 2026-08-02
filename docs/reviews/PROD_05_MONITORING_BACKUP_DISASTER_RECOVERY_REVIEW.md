# PROD-05 Monitoring, Backup and Disaster Recovery Review

## Decision

- State: `BLOCKED_SAFELY`
- Decision: `BLOCKED`
- Baseline: `f84dd708531754efce43317cb99a0ad5174e5297`
- Phase commit: `PENDING_UNTIL_COMMIT`

## Implemented

- Redis-backed Prometheus counters for HTTP requests, duration, and application errors.
- Protected metrics and operations-health endpoints using a dedicated server-side token.
- Live gauges for PostgreSQL, Redis, disk, CPU/RAM, Ollama, n8n, login failures, AI governance, uploads/extractions, sessions, database connections, and queue depth.
- JSON logs with route templates and correlation IDs; body, query, tokens, prompt text, customer files, and identity are excluded.
- Backup tooling for PostgreSQL, media, n8n data, versioned workflows, checksums, release metadata, and safety gates.
- Restore tooling that rejects unsafe archives and targets only a temporary database/filesystem.
- Prometheus scrape/alert rules, Grafana dashboard contract, backup policy, and eight operator runbooks.

## Validation

- Compile: PASS
- Django check: PASS
- Migration drift: PASS; no migration created
- Focused tests: 23 PASS
- Full regression: 500 PASS
- Migration regression: 238 PASS
- Ruff/format/mypy: PASS in changed scope
- Bandit: zero Medium/High/Critical findings in changed scope
- Mandatory Ollama: real response, schema valid, fallback false, final decision BLOCKED

## Blocking Gate

The environment denied Docker API access and rejected the exact escalation request because its Codex usage limit was reached. Therefore no real PostgreSQL/media/n8n backup exists and the isolated restore test cannot truthfully run. Dependency audit was also unable to access PyPI; requirements are unchanged from PROD-04.

No fake backup, restore result, or PASS evidence was created. No production data, route, infrastructure, or deployment was modified.

## Required Recovery

1. Restore Docker API access for the operator session.
2. Run `python scripts/prod05_backup.py`.
3. Run `python scripts/prod05_restore_test.py <package> --output <report>`.
4. Rerun dependency audit with network access.
5. Regenerate evidence and run mandatory local Ollama review.
6. Advance only if review is schema-valid PASS with zero Critical/High findings.

## Safety Gates

```json
{
  "human_approval_required": true,
  "auto_merge": false,
  "auto_deploy": false,
  "approval_bypass_detected": false
}
```

PROD-06 was not started.
