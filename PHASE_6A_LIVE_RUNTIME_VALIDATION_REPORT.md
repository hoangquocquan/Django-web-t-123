# Phase 6A Live Runtime Validation Report

Timestamp: 2026-09-16 22:37:47 +09:00 (Asia/Tokyo)

## Final verdict

`PASS_PHASE_6A_LIVE_RUNTIME_VALIDATION`

Phase 6A completed static and live PostgreSQL/Redis/Django/Vite validation with the approved Django host-port override `8001`. The unrelated `mecprecision-vietnam-web-1` container remained healthy and unchanged on host port `8000` for the entire validation.

After evidence collection, cleanup was performed only with:

```powershell
.\scripts\phase6\Stop-Phase6.ps1
```

No prune, `wsl --shutdown`, Docker Desktop restart, unrelated resource mutation, stage, commit, push, reset, clean, stash, deploy, or Phase 6B action occurred.

## Scope and source decision

The requested configurable Django host-port solution already existed and passed inspection:

1. `docker-compose.phase6.yml` publishes `127.0.0.1:${PHASE6_DJANGO_PORT:-8000}:8000`.
2. `.env.phase6.example` documents `PHASE6_DJANGO_PORT=8000` and `PHASE6_VITE_PORT=8443`.
3. `Initialize-Phase6Environment.ps1` generates the same non-secret defaults.
4. `Start-Phase6.ps1` accepts `-DjangoPort` and `-VitePort`, validates both ports, exports the selected values for Compose, and sets `VITE_DJANGO_ORIGIN` to the selected Django host port.
5. `phase6.config.ts` keeps Vite proxy routing loopback-only and proxies only root-relative `/api`.
6. Phase 6A frontend tests cover the default origin and explicit alternate loopback ports.
7. The Phase 6 runbook already documents synchronized alternate backend/frontend port usage.

Therefore, no new port implementation or refactor was necessary. The existing override was used as authorized:

- Default Django host port: `8000`.
- Approved validation override: `8001`.
- Vite host port: `8443`.
- Django container port: `8000`.
- Effective binding: `127.0.0.1:8001 -> 8000/tcp`.
- Effective Vite proxy target: `http://127.0.0.1:8001`.

The base `docker-compose.yml` was not used or modified.

## Configuration handling

The ignored `.env.phase6` file existed. Validation confirmed without printing values that:

- every required variable name was present;
- no `CHANGE_ME` placeholder remained.

The file contents, credentials, passwords, secret key, Redis password, database URL, and metrics token were never printed or copied into this report.

## Read-only preflight

### Windows ports

Immediately before startup:

| Port | Listener count | Result |
| ---: | ---: | --- |
| `8001` | 0 | Free; approved for Phase 6A Django |
| `8443` | 0 | Free; approved for Phase 6A Vite |

### Docker ports and engine

- Docker client: `29.4.3`.
- Docker server: `29.4.3`.
- No running Docker container published host port `8001`.
- No running Docker container published host port `8443`.
- Compose config resolved Django target `8000`, published port `8001`, host IP `127.0.0.1`, protocol `tcp`.
- Compose config parser completed successfully.

### Unrelated runtime baseline

Before Phase 6A startup:

```text
container ID: dfd724919eb2d12cb6d823cfeb8993478efe286b1f042edbdd15fc435a1d3452
name: mecprecision-vietnam-web-1
state: running
health: healthy
started: 2026-09-16T12:51:16.76564653Z
restart count: 0
ports: 0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
```

The unrelated runtime was not stopped, restarted, inspected for secrets, or otherwise modified.

## Static validation

### Frontend

| Command/check | Result |
| --- | --- |
| `pnpm run test:phase6a` | PASS — 4/4 tests |
| `pnpm run test` | PASS — 128/128 tests |
| `pnpm run typecheck` | PASS |
| `pnpm run format:check:phase6a` | PASS |

The full frontend suite included and passed the completed Phase 5C RFQ corrective tests. No RFQ corrective source file was modified during this Phase 6A task.

### Backend

| Command/check | Result |
| --- | --- |
| `python manage.py check` | PASS — no issues |
| `python manage.py makemigrations --check --dry-run` | PASS — no changes detected |
| Phase 6A configuration/write-boundary tests | PASS — 17/17 tests |

### PowerShell and Compose

- `Initialize-Phase6Environment.ps1`: parser PASS.
- `Start-Phase6.ps1`: parser PASS.
- `Stop-Phase6.ps1`: parser PASS.
- Compose config with `PHASE6_DJANGO_PORT=8001`: PASS.
- Effective loopback binding: `127.0.0.1:8001 -> container 8000`.

### Diff validation

- `git diff --check`: PASS, exit code `0`.
- Output contained only existing LF-to-CRLF warnings; no whitespace error was reported.

## Live startup

The authorized command was:

```powershell
.\scripts\phase6\Start-Phase6.ps1 -DjangoPort 8001
```

The helper reported:

```text
Django port 8001 is empty.
Vite port 8443 is empty.
ready: Phase 6A Django, PostgreSQL, Redis, and Vite passed bounded readiness and routing smoke checks.
```

The sanitized startup result was:

```json
{
  "code": "ready",
  "message": "Phase 6A Django, PostgreSQL, Redis, and Vite passed bounded readiness and routing smoke checks.",
  "project": "django-web-t-123-phase6"
}
```

## Live resources

| Resource | Image | State | Exposure |
| --- | --- | --- | --- |
| `django-web-t-123-phase6-postgres` | `postgres:16-alpine` | Running, healthy | Internal `5432` only |
| `django-web-t-123-phase6-redis` | `redis:7-alpine` | Running, healthy | Internal `6379` only |
| `django-web-t-123-phase6-django` | `django-web-t-123-phase6-django:local` | Running, healthy | `127.0.0.1:8001 -> 8000` |
| Vite Node process | Local dependency runtime | Running during evidence collection | `127.0.0.1:8443` |

All Phase 6A containers were attached only to `django-web-t-123-phase6-internal`. PostgreSQL and Redis had no host-published port.

## PostgreSQL and cache evidence

Live Django reported only the following non-secret configuration facts:

```json
{
  "database_engine": "django.db.backends.postgresql",
  "database_vendor": "postgresql",
  "database_host": "postgres",
  "database_name_configured": true,
  "cache_backend": "django.core.cache.backends.redis.RedisCache",
  "cache_location_uses_redis": true
}
```

This proves the live Phase 6A Django process used PostgreSQL instead of SQLite and used the configured Redis cache backend.

The public readiness view executes a PostgreSQL `SELECT 1`, performs a bounded Redis cache set/get check, and returns `503` on either dependency failure. Its live response returned `200 ready`, proving both dependencies were available.

## Migration evidence

- Startup ran `python manage.py migrate --noinput` successfully.
- Startup ran `python manage.py migrate --check` successfully.
- An independent live-container `migrate --check` exited successfully.
- `showmigrations --plan` listed the complete current migration chain as applied (`[X]`).
- No unapplied migration was reported.

## HTTP endpoint evidence

### Direct Django on port 8001

| Endpoint | Status | Body |
| --- | ---: | --- |
| `/api/v1/phase6/live/` | 200 | `{"success":true,"data":{"status":"live"}}` |
| `/api/v1/phase6/ready/` | 200 | `{"success":true,"data":{"status":"ready"}}` |

### Browser-equivalent Vite on port 8443

| Endpoint | Status | Evidence |
| --- | ---: | --- |
| `/` | 200 | Vite frontend served successfully |
| `/api/v1/phase6/live/` | 200 | Same live payload as direct Django |
| `/api/v1/phase6/ready/` | 200 | Same ready payload as direct Django |

This proves the root-relative Vite `/api` proxy reached the Phase 6A backend on the selected host port `8001`.

The launcher also completed bounded smoke requests for the Foundation login route and canonical RFQ route without receiving a `404`.

## Allowed-host and origin sanity

Live settings reported:

```json
{
  "allowed_hosts": ["127.0.0.1", "localhost"],
  "csrf_trusted_origins": ["http://127.0.0.1:8443"]
}
```

Runtime behavior:

- Valid `Host: 127.0.0.1:8001` returned `200`.
- Untrusted `Host: untrusted.example.invalid` returned `400`.
- The configured CSRF trusted origin matched the actual Vite origin used for validation.

No remote origin or wildcard host was introduced.

## Business-data preservation

Live counts after migration and smoke validation showed:

- `SalesRfq`: 0.
- `SalesRfqLine`: 0.
- `SalesQuotation`: 0.
- `TransactionOrder`: 0.
- `OrderProgressEvent`: 0.
- `AuditEvent`: 0.
- All other Sales workflow records: 0.
- Customer, material, product, inventory transaction, and other mutable business records: 0.

One inventory warehouse existed as migration/seed baseline. No RFQ, quotation, order, progress, decision, audit, or other workflow record was created by live connectivity validation.

## Unrelated runtime coexistence evidence

During live validation, `mecprecision-vietnam-web-1` still had exactly the original evidence:

```text
container ID: dfd724919eb2d12cb6d823cfeb8993478efe286b1f042edbdd15fc435a1d3452
state: running
health: healthy
started: 2026-09-16T12:51:16.76564653Z
restart count: 0
ports: 0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
```

After cleanup, the same container ID, start time, health, restart count, and port mapping were observed again. The unrelated Compose project remained `mecprecision-vietnam running(5)`.

## Cleanup evidence

Only the scoped stop helper was used:

```powershell
.\scripts\phase6\Stop-Phase6.ps1
```

Results:

- Vite ownership state was verified and its recorded process was stopped.
- Exactly the three Phase 6A containers were stopped and removed.
- `django-web-t-123-phase6-internal` was removed.
- `django-web-t-123-phase6-postgres-data` was preserved.
- `django-web-t-123-phase6-media` was preserved.
- Port `8001` listener count after cleanup: 0.
- Port `8443` listener count after cleanup: 0.
- `.phase6/vite-process.json` was removed.
- No Phase 6A container or network remained.
- No unrelated Docker resource was stopped or removed.

## Git/worktree preservation

- Branch: `codex/demo-database-validation`.
- HEAD: `01f15037e64d6c565e8444dc99eee6c9eb7c37f4`.
- HEAD subject: `phase5e: repair progress reconciliation evidence matching`.
- Staged file count: 0.
- Existing modified and untracked worktree files were preserved.
- `.env.phase6` was not printed, rewritten, staged, or committed.

No reset, restore, checkout, clean, stash, stage, commit, push, merge, rebase, or deploy command was run.

## Files changed by this validation task

- `PHASE_6A_LIVE_RUNTIME_VALIDATION_REPORT.md` — updated with current preflight, live evidence, coexistence proof, cleanup evidence, and final verdict.

No implementation file required modification because the safe configurable override already existed and passed live validation.

Runtime-only effects were limited to ignored `.phase6/` logs/state and the preserved Phase 6A-owned Docker volumes.

## Remaining blockers

- Phase 6A live-runtime blocker: none.
- Phase 6B remains out of scope and was not started.
- Existing unrelated dirty worktree changes remain uncommitted and untouched.

Final verdict: `PASS_PHASE_6A_LIVE_RUNTIME_VALIDATION`.
