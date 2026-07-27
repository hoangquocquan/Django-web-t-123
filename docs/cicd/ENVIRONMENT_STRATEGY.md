# Environment Strategy

## Development

Purpose:

- Fast local development and safe experimentation.

Configuration:

- Local `.env`.
- SQLite or local development database.
- Debug allowed only locally.

Data policy:

- Demo data only.
- No production secrets.
- No production customer files.

Deployment method:

- Manual local run.
- Optional automatic deployment to developer sandbox later.

## Testing

Purpose:

- Automated validation and regression checks.

Configuration:

- Test settings.
- Temporary databases.
- Mocked external services where possible.

Data policy:

- Synthetic fixtures.
- No production secrets.

Deployment method:

- CI test runner.
- No public exposure.

## Staging

Purpose:

- Production-like validation before release.

Configuration:

- Production-like Django settings.
- Production-like web server/proxy.
- Separate database and secrets.
- Monitoring enabled.

Data policy:

- Sanitized data only unless formally approved.
- No uncontrolled production data copies.

Deployment method:

- Manual gated deployment.
- Health check required after deployment.
- AI-assisted review can run, but human approval remains required.

## Production

Purpose:

- Live customer/business traffic.

Configuration:

- Debug disabled.
- Real secrets from secret manager.
- HTTPS enforced.
- Logging, monitoring, backup, and alerting enabled.

Data policy:

- Real customer data.
- Strict access control.
- Backup and retention policy required.

Deployment method:

- Manual approval gate.
- Immutable artifact deployment.
- Post-deployment health check.
- Rollback plan ready before change starts.

