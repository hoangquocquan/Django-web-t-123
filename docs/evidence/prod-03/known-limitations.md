# PROD-03 Known Limitations

- The 2FA layer creates and verifies one-time challenges, but delivery through an
  email/authenticator adapter remains an operator-configured integration.
- The malware scanner is a fail-closed adapter contract with local EICAR
  detection; a production ClamAV service is not configured in this phase.
- Login throttling is database-backed. Distributed Redis consistency for all AI
  and auth worker limits is a PROD-04 objective.
- Docker Scout was attempted but requires Docker ID login. Dependency audits,
  Bandit, secret scanning, runtime artifact scanning, and non-root checks passed.
- No staging or production deployment occurred.
