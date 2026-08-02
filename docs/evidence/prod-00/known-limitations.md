# PROD-00 Known Limitations

- Docker daemon is unavailable although Docker Compose configuration can parse.
- PostgreSQL client/runtime is not installed or reachable from this shell.
- Redis client/runtime is not installed or reachable from this shell.
- Live n8n is not reachable on localhost port 5678.
- Local runtime SQLite files, logs, backup artifacts, and three ZIP files exist
  outside Git. They are not staged or deleted.
- One tracked training IIS log is documentation/test evidence, not production PII.
- Tracked Compose configuration contains local-only development credentials;
  PROD-02 must replace them with required environment inputs before production.

These baseline limitations cannot be reported as production runtime PASS.
