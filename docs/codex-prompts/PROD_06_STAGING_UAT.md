# PROD-06 Staging UAT And Production Readiness Validation

## Objective

Validate the integrated platform in a production-like local staging stack before
preparing a controlled deployment handover.

## Scope

- Validate Django/Gunicorn, PostgreSQL, Redis, n8n, Ollama and proxy HTTPS behavior.
- Execute role, CRM, Sales, Knowledge/RAG, AI Sales, AI Agent, governance, n8n and operations UAT.
- Run bounded read-only load smoke with p50, p95 and p99 evidence.
- Run security, dependency, migration, backup, restore and rollback checks.
- Require a real, schema-valid local Ollama review of the actual phase diff.

## Safety Gates

Human approval remains mandatory. No merge, push, tag, production deployment,
automatic business action, automatic phase approval or production restore is allowed.

## Acceptance Criteria

Every deterministic gate passes; environment limitations are recorded honestly;
the Ollama review uses no fallback and reports zero Critical/High findings.
