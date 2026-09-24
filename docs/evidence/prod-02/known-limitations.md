# PROD-02 Known Limitations

- Docker Scout could not scan the image without a Docker ID login. Python
  runtime and development dependencies were audited successfully with pip-audit.
- The local validation stack uses process-only throwaway credentials and disables
  PostgreSQL TLS inside the private Docker network. A real production secret
  manager, TLS termination, and managed database policy still require human
  environment configuration.
- The health payload retains `sqlite_version` only for the legacy API contract;
  production readiness now probes the Django PostgreSQL and Redis connections.
- A pre-existing Phase 10 dry-run PostgreSQL container was observed and left
  untouched. PROD-02 did not remove orphan containers or volumes.
- Live n8n is not part of this phase and remains unverified.
- Three user ZIP files remain untracked and untouched.
