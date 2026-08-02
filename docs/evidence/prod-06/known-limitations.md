# PROD-06 Known Limitations

- Local TLS is represented by the trusted reverse-proxy header contract; no public certificate or external staging deployment was created.
- Docker Scout was blocked because it may send image metadata to an external service. The result is `BLOCKED_BY_ENVIRONMENT`, not PASS. Local dependency and source security scans still ran.
- Repository-wide Ruff formatting and broad Mypy include inherited debt outside PROD-06. Scoped PROD-06 Ruff/Mypy pass; full regression remains the behavioral gate.
- Load smoke is bounded to 20 virtual users and 140 read-only requests. It validates readiness behavior, not capacity planning for a declared production SLA.
- Three user ZIP files remain untracked and were neither inspected nor staged.
