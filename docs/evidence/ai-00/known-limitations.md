# AI-00 Known Limitations

- Docker daemon is unavailable and `C:/Users/hoang/.docker/config.json` reports access denied.
- Redis has not been runtime-validated.
- PostgreSQL/pgvector has not been runtime-validated.
- Existing knowledge index still uses hash embeddings until AI-01.
- Existing AI review fallback is not fail-closed until AI-05.
