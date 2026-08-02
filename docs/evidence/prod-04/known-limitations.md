# Known Limitations

- The current vector store uses PostgreSQL-backed Django JSON vectors and performs in-process cosine ranking. It is correct for the present small dataset but should move to pgvector before high-scale use.
- Docker Scout could not run without Docker ID authentication; dependency audits, Bandit, image artifact inspection, and non-root validation passed.
- Whole-repository Ruff/format and default mypy remain affected by documented legacy formatting debt and duplicate `config` package names. Changed-file checks pass.
- n8n is validated on the local production-like stack. Real production secrets, TLS termination, external worker topology, merge, deployment, and production activation were not configured.
- Human approval remains mandatory. No phase, merge, or deployment is automatic.
