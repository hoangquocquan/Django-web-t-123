# Phase 6D staging-like operations runbook

This runbook covers the isolated portfolio-demo stack only. It does not certify
public production, operate the base `docker-compose.yml`, or authorize Phase 6E.

## Topology and prerequisites

The production-like path is browser -> loopback static gateway on 8443 -> the
single Django application backend -> private PostgreSQL 16 and Redis 7. The
gateway serves the Vite production build, proxies `/api/`, and reads the named
media volume read-only. Django remains the only application backend.

Required tools are Docker Desktop/Compose, PowerShell 7, Python 3.12, Node 22,
and pnpm 10.34.3. Keep unrelated `mecprecision-vietnam` on 8000 untouched; use
8001 for Phase 6D Django and 8443 for the static gateway.

Create the ignored environment file once:

```powershell
pwsh -NoProfile -File scripts/phase6/Initialize-Phase6Environment.ps1
```

The required secret names are documented in `.env.phase6.example`. Never print,
commit, paste into a report, or bake the ignored file into an image. Replace a
placeholder file by deleting it manually only after confirming the exact path,
then rerun the initializer. Production settings reject missing service URLs,
SQLite, wildcard hosts/origins, non-empty CORS, and malformed trusted origins.

## Start, verify, migrate, and stop

Read-only preflight comes first: check `docker compose ls`, `docker ps`, and
listeners on 8001/8443. Do not stop or inspect owners of unrelated listeners.

```powershell
pwsh -NoProfile -File scripts/phase6/Start-Phase6D.ps1 -DjangoPort 8001 -FrontendPort 8443
```

The helper always pulls/builds current source, waits within explicit bounds,
starts only the Phase 6 project, applies migrations before Django/frontend, and
fails closed. Verify both paths:

```powershell
Invoke-WebRequest http://127.0.0.1:8001/api/v1/phase6/live/
Invoke-WebRequest http://127.0.0.1:8443/api/v1/phase6/ready/
Invoke-WebRequest http://127.0.0.1:8443/
```

Manual diagnosis may run `migrate --check` only with the exact project, env,
and Compose file described in `LOCAL_FULL_STACK.md`. Never run migrations
against an unclassified database URL.

Stop without deleting volumes:

```powershell
pwsh -NoProfile -File scripts/phase6/Stop-Phase6.ps1
```

Logs and sanitized startup results are under ignored `.phase6/logs/`; container
logs remain on stdout/stderr. Never copy raw logs into reports before checking
for credentials, bearer tokens, email addresses, or request bodies.

## Bounded recovery

- Port conflict: choose explicit unused Phase 6 ports; never terminate the owner.
- Docker Desktop unavailable: stop, record the blocker, and ask the Owner to
  recover Docker. Do not run `wsl --shutdown`, restart Docker, or prune.
- PostgreSQL unavailable: readiness must return 503. Restore the Phase 6 service
  only, wait healthy, then re-run readiness and `migrate --check`.
- Redis unavailable: readiness must return 503. Redis contains cache/session
  acceleration only; restart the Phase 6 Redis service and allow cache rebuild.
- Invalid config: correct the ignored env file; never weaken production settings.
- Failed migration: stop application startup, preserve the database volume and
  logs, take a backup if readable, and diagnose. Do not fake migration rows.
- Stale image: rerun `Start-Phase6D.ps1`; its `build --pull` step prevents tagged
  local images from silently replacing current source.
- Failed readiness: keep the gateway out of service and distinguish database,
  cache, Django, and gateway health before one bounded restart.

Forbidden recovery actions are any Docker/system prune, removal of ambiguous
volumes, base-stack startup, unrelated service restart, or forced destructive
database repair.

## Secret rotation and rollback

Rotate one ignored secret at a time during a maintenance window. Database or
Redis credentials must be changed at the service and env file together; rotate
the Django key only with awareness that signed sessions become invalid. Rotate
the metrics token and restart the Phase 6 stack. Verify that old credentials
fail and health/auth still pass without logging either value.

Rollback is operational, not a Git reset: preserve the current database/media,
take a verified backup, stop Phase 6, select an Owner-approved prior image/source
revision, confirm migration compatibility, and start with the same named data
volumes. If the prior revision cannot read the current schema, restore only to a
new isolated database and escalate; never downgrade or overwrite the live Phase
6 database ad hoc.

Canonical workflow rows, entity timelines, audit records, login/security events,
and accepted/conversion history are audit-sensitive and must not be edited or
deleted to make a demo look clean. Media referenced by those records must be
backed up consistently with PostgreSQL.
