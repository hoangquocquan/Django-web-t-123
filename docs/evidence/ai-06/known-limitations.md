# AI-06 Known Limitations

- `N8N_RUNTIME_NOT_VERIFIED`: workflow JSON and controller contracts pass, but
  no live n8n server or webhook is configured locally.
- Redis is not configured. Governance uses the explicit Django-cache
  development fallback, which is not multi-worker or restart safe.
- `pip-audit` could not refresh vulnerability data because outbound access to
  PyPI is blocked in the execution environment. The command and real network
  error are preserved in evidence.
- Repository-wide Ruff checks retain inherited style debt. Both files changed
  by AI-06 pass Ruff check and format validation.
- A cumulative mypy run retains missing Django/DRF stubs and generated
  migration annotation debt. The AI-06 changed source passes mypy with missing
  third-party imports ignored.
- Docker Compose configuration parses successfully, but the Docker daemon is
  not running and Docker Desktop configuration access remains restricted.
- The local development vector store uses Django JSON storage rather than a
  production pgvector service.

None of these limitations enables automatic merge, deployment, AI
self-approval, or bypass of the required final human approval.
