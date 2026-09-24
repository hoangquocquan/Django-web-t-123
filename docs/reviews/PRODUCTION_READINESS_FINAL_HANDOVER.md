# Production Readiness Final Handover

## Release Candidate

- Branch: `codex/production-readiness-full`.
- Production-readiness baseline: `65b77beefbb80f715baf5d30f2a70c22d7bb5d44`.
- PROD-06 implementation: `3aa911026eeef07d0dccff42588505380d0baea4`.
- PROD-06 completion metadata: `ad930d0`.
- Release state: documentation package only; not deployed.

## Controlled Deployment Procedure

1. Human release approval.
2. Freeze the approved commit and verify a clean checkout.
3. Confirm an off-host PostgreSQL/media/n8n backup and checksum manifest.
4. Build the exact Docker image from the approved commit.
5. Run dependency, source and image security scans in the approved environment.
6. Deploy to staging and execute health, migration and business smoke tests.
7. Obtain a second human production approval.
8. Deploy the immutable image through the organization deployment system.
9. Run migrations once, then collect static assets if the target requires it.
10. Verify health, authentication, CRM, Sales, Knowledge, AI and n8n.
11. Monitor error rate, latency, dependencies, queues and capacity.

This document defines the procedure only. None of these deployment actions was
executed by PROD-07.

## Required Environment Names

`SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`,
`REDIS_URL`, `METRICS_BEARER_TOKEN`, `N8N_ENCRYPTION_KEY`,
`N8N_WEBHOOK_SECRET`, `OLLAMA_HOST`, `OLLAMA_MODEL`,
`OLLAMA_EMBEDDING_MODEL`, `OLLAMA_REVIEW_MODEL`.

Values must come from the target secret manager and must never be copied into
Git, tickets, screenshots or review artifacts.

## Post-Deployment Verification

- Django, PostgreSQL, Redis, Ollama and n8n health are ready.
- Metrics endpoint is authenticated and scrape succeeds.
- Login/logout/role checks pass for approved test accounts.
- CRM customer, interaction and task smoke passes.
- Sales lead, quotation approval and handoff smoke passes.
- Knowledge retrieval has citations; no-context behavior is safe.
- AI Sales remains draft-only and Agent remains read-only.
- No Critical/High security regression or secret leakage appears.
