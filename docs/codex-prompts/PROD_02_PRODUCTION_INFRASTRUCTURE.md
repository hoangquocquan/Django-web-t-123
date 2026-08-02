# PROD-02 Production Settings And Infrastructure

## Objective

Provide a fail-fast Django production configuration and a reproducible,
production-like local container runtime backed by PostgreSQL and Redis.

## Scope

- Require production secret, hosts, PostgreSQL URL, and Redis URL.
- Enable secure proxy/cookie/HSTS settings and stdout logging.
- Run Gunicorn as a non-root user with WhiteNoise static assets.
- Keep PostgreSQL and Redis on a private Compose network with health checks.
- Exclude SQLite, databases, ZIP, backups, logs, and uploads from the image.
- Validate migrations on an empty PostgreSQL database and Redis cache access.

## Safety Gates

```json
{
  "human_approval_required": true,
  "auto_merge": false,
  "auto_deploy": false,
  "approval_bypass_detected": false
}
```

The Compose stack is local validation only. It does not deploy staging or
production and uses process-local throwaway validation credentials.

## Acceptance Criteria

- Missing required production variables stop Django startup.
- SQLite and non-Redis URLs are rejected by production settings.
- Production Django check, PostgreSQL migrations, Redis probe, image health,
  non-root check, dependency audit, focused tests, and regression pass.
- No runtime DB, backup, secret, or ZIP exists in the image or staged files.
- Mandatory local Ollama review passes without fallback or Critical/High findings.

## Rollback

Revert the dedicated PROD-02 commit and use development settings. Stop the local
Compose services without deleting volumes unless a human explicitly approves
data removal.
