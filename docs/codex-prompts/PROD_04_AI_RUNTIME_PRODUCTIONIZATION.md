# PROD-04 - Ollama, Redis, n8n and AI Runtime Productionization

## Objective

Productionize the local-only AI runtime while preserving human approval and read-only AI behavior.

## Safety Gates

- Ollama endpoints and models are server-owned allowlists.
- Redis enforces distributed request limits and inference capacity.
- RAG reports model, vector coverage, stale indexes, and citation quality.
- AI Sales only produces drafts; AI Agent tools remain read-only.
- n8n requires HMAC authentication and never merges, deploys, or advances a phase.
- Human approval is always required for protected actions.

## Validation

Focused tests, full regression, production Compose runtime, Redis consistency, live n8n webhook, and mandatory local Ollama review are required before PROD-05.
