# Production Readiness Known Issues

## Release Warnings

- Docker Scout was blocked in this environment because it may transmit image
  metadata externally. Run the approved private-registry image scanner before
  production approval.
- Local staging uses the trusted reverse-proxy HTTPS contract, not a public CA
  certificate. Validate the real load balancer/TLS chain in target staging.
- The 20-user, 140-request load smoke is not a production capacity SLA. Execute
  organization-specific capacity and soak tests before setting an SLA.
- Repository-wide Ruff formatting and broad Mypy retain inherited debt. Scoped
  phase checks and all behavior tests pass.
- Three user-owned ZIP files are untracked and excluded from this release.

## Operational Follow-Up

- Define named incident commander, database owner and deployment operator.
- Store backups off-host with retention and periodic restore drills.
- Configure production alert destinations and on-call escalation.
- Confirm Ollama host capacity and model warm-up behavior under target load.

These warnings do not authorize bypassing any human gate.
