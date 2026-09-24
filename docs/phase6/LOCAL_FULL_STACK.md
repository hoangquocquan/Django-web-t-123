# Phase 6A local full-stack foundation

Phase 6B browser validation is documented in
[`PHASE_6B_BROWSER_E2E.md`](PHASE_6B_BROWSER_E2E.md).

Phase 6D production-static startup and operations are documented in
[`OPERATIONS.md`](OPERATIONS.md), with the isolated restore drill in
[`BACKUP_RESTORE.md`](BACKUP_RESTORE.md).

## Architecture and ownership

The local production-like path is browser → Vite on `127.0.0.1:8443` →
root-relative `/api/...` proxy → Django on `127.0.0.1:8000` → internal-only
PostgreSQL 16 and Redis. Production remains one same-origin React + `/api`
deployment; Django is the only application backend.

Every container, network, and persistent volume is owned by the exact Compose
project prefix `django-web-t-123-phase6`. The isolated definition is
`docker-compose.phase6.yml`. It does not attach an external network or volume,
and publishes only Django to loopback. PostgreSQL and Redis are internal-only.

AI FACTORY, n8n, Zalo, 9Router, Codex Bridge, AI/OCR, and external automation
are unrelated and must not be inspected, started, stopped, or configured for
this workflow. Never run broad Docker cleanup commands.

## Required software and configuration

Install Docker Desktop with Compose, Python 3.12 for static/backend tests,
Node.js 22, pnpm 10, and PowerShell 7. Copy `.env.phase6.example` to the ignored
root file `.env.phase6`; copy `figma_make_frontend/.env.example` only when
running Vite without the helper.

Required secret-bearing variable names are `PHASE6_SECRET_KEY`,
`PHASE6_POSTGRES_DB`, `PHASE6_POSTGRES_USER`, `PHASE6_POSTGRES_PASSWORD`,
`PHASE6_REDIS_PASSWORD`, and `PHASE6_METRICS_BEARER_TOKEN`. Never paste their
values into commands, logs, reports, or Git. Non-secret routing names are
`PHASE6_DJANGO_PORT`, `PHASE6_VITE_PORT`, and `VITE_DJANGO_ORIGIN`.

## Exact start and stop sequence

From the repository root:

```powershell
pwsh -NoProfile -File scripts/phase6/Initialize-Phase6Environment.ps1
pwsh -NoProfile -File scripts/phase6/Start-Phase6.ps1
```

The helper validates configuration names without displaying values, checks
only ports 8000 and 8443, starts only Phase 6 dependencies, runs `migrate` and
`migrate --check`, starts Django and Vite asynchronously, and performs bounded
liveness, readiness, login-route, and canonical RFQ-route smoke checks. Logs
and process ownership state stay under ignored `.phase6/`.

Stop safely with:

```powershell
pwsh -NoProfile -File scripts/phase6/Stop-Phase6.ps1
```

The stop helper verifies the recorded Vite PID, start time, and executable name
before stopping it, then targets only `django-web-t-123-phase6`. To delete only
the named Phase 6 volumes after evidence is no longer needed, add
`-RemoveOwnedVolumes`. It never runs prune or touches another Compose project.

## Ports, readiness, and migrations

The defaults are Django 8000 and Vite 8443. A listener on either port causes a
fail-closed result; no owning process is stopped or inspected. Explicit
alternates must be supplied together:

```powershell
pwsh -NoProfile -File scripts/phase6/Start-Phase6.ps1 -DjangoPort 18000 -VitePort 18443
```

The helper then sets the Vite proxy target consistently to
`http://127.0.0.1:18000`. Remote, HTTPS, credentialed, path-bearing, malformed,
or portless proxy targets are rejected. All subprocesses and HTTP probes have
explicit bounds. Liveness (`/api/v1/phase6/live/`) checks only the Django
process; readiness (`/api/v1/phase6/ready/`) requires both the database and
cache.

Manual migration commands, if diagnosis requires them, must retain the exact
project, env file, and Compose file:

```powershell
docker compose -p django-web-t-123-phase6 --env-file .env.phase6 -f docker-compose.phase6.yml run --rm django python manage.py migrate --noinput
docker compose -p django-web-t-123-phase6 --env-file .env.phase6 -f docker-compose.phase6.yml run --rm django python manage.py migrate --check
```

## Tests

Frontend gates are `typecheck`, `typecheck:phase5a`, `test:phase5a` through
`test:phase5e`, `test:phase6a`, full `test`, `format:check:phase6a`, and
`build`. Backend gates are Django `check`, `makemigrations --check --dry-run`,
the focused Phase 6A configuration/write-boundary tests, the Phase 4D order
boundary suite, and the full configured pytest suite. The current Phase 5
minimums remain 12/18/30/22/38 and 120 total before Phase 6A additions.

## Troubleshooting and Phase 6B transition

- `port_collision`: choose explicit unused alternate ports; do not stop the listener.
- `configuration_missing`: add the named variable to ignored `.env.phase6`.
- `failed:migrate` or `failed:migrate-check`: inspect only `.phase6/logs/` and
  preserve the database volume for diagnosis.
- `readiness_timeout`: distinguish dependency, Django, and Vite log names;
  stop with the exact safe command above.

Phase 6A establishes routing, isolation, settings validation, and legacy write
containment only. Phase 6B business screens, form submission, browser workflow
automation, UAT, staging release, and external integrations remain out of scope.
