# AI System Hardening V2 Known Issues

1. `N8N_RUNTIME_NOT_VERIFIED`: workflow/controller tests pass, but no live n8n
   server or webhook is configured.
2. Redis is not configured locally; governance uses the explicit Django-cache
   development fallback.
3. `pip-audit` is blocked by denied outbound PyPI access, so current advisory
   metadata could not be refreshed.
4. Repository-wide Ruff and cumulative mypy have inherited baseline debt.
   Files changed by AI-06 pass their scoped checks.
5. Docker Compose configuration passes, but the Docker daemon is unavailable
   and local Docker config access has a permission warning.
6. The development vector store uses Django JSON storage rather than a
   production pgvector deployment.
7. The Ollama review prose summary generically references phase 13.8. The
   structured review artifact itself is phase AI-06 and passed all mandatory
   correlation, diff, schema, safety, and finding gates.

These are not approval bypasses. A human must consider them before any later
release or deployment decision.
