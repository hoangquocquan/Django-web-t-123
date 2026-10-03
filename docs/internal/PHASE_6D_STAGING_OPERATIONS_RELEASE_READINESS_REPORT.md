# Phase 6D Staging, Operations, and Release-Readiness Report

Date: 2026-09-17 (Asia/Tokyo)

## Scope and boundary

Phase 6D hardened and validated the portfolio production-demo target. It did
not certify a public production deployment, start Phase 6E, deploy, stage,
commit, push, reset, clean, stash, prune, restart Docker Desktop, stop an
unrelated service, or use the base `docker-compose.yml`.

The validated topology was browser -> loopback production-static gateway on
8443 -> the single Django backend -> private PostgreSQL and Redis. The unrelated
`mecprecision-vietnam` stack remained on 8000 throughout.

## Release-readiness matrix

| Area | Result | Evidence / disposition |
|---|---|---|
| Production Django settings | READY | `DEBUG=False`; production import fails closed; live container used production settings. |
| Environment-variable contract | READY | Required secret/service names are documented and checked without displaying values. |
| Secret handling | READY | Placeholder/control-character rejection, ignored env, no secret build inputs, scoped pattern scan and image scan passed. |
| PostgreSQL | READY | Production rejects non-PostgreSQL URLs; PostgreSQL 16 health, migrations, outage/recovery, backup/restore passed. |
| Redis | READY | Authenticated Redis URL required; private health, cache readiness, outage/recovery passed. |
| Static files/frontend | READY | Current Vite production build runs in a non-root read-only Nginx static gateway; no sourcemaps in the image. |
| Media | READY | Named persistent volume is writable only by Django and mounted read-only at the gateway; operational consistency is documented. |
| `ALLOWED_HOSTS` | READY | Explicit hosts required; wildcard, URL, path, and whitespace entries rejected. |
| CSRF trusted origins | READY | Explicit HTTP(S) origins only; wildcard/credentials/path/query/fragment rejected; HTTPS required when SSL redirect is enabled. |
| CORS | READY | Production same-origin topology requires an empty allowlist. |
| HTTPS/security settings | READY | Secure cookies, proxy SSL header, HSTS defaults, nosniff, referrer, opener, frame, CSP and permissions policy are configured. Local loopback validation intentionally disabled SSL redirect. |
| Logging | READY | JSON stdout/stderr logging with safe fields; request bodies and credentials excluded; build-generated log removed from image. |
| Liveness/readiness | READY | Liveness is dependency-free; readiness requires database and cache; gateway health uses readiness. |
| Docker image/runtime | READY | Current source built with `--pull`; backend user `appuser`, gateway user `101`; both read-only and healthy; images contain no env/database/dump/log artifacts. |
| Migrations/startup ordering | READY | Dependencies -> migrate -> `migrate --check` -> Django -> gateway, all bounded and fail-closed. |
| Backup/restore | READY | 304,179-byte custom PostgreSQL dump restored into a temporary Phase 6 database; 61 public tables readable and migration fingerprint matched; temporary DB dropped. |
| Operational rollback | READY | Backup-first, migration-compatible, isolated-restore and Owner-approval procedure documented; no destructive Git rollback. |
| Frontend production build | READY | Vite production build and production-static browser UAT passed through 8443. |
| API origin/proxy | READY | Root-relative `/api` routes proxy internally to `django:8000`; no second application backend. |
| CI definition | READY | CI includes Phase 6D backend/frontend contracts and Compose profile validation. |
| Remote CI run status | NEEDS_HARDENING | No GitHub Actions run was requested or observed from this uncommitted worktree; all equivalent local gates passed. |
| Runbooks/checklist | READY | Operations, backup/restore, local full-stack links, and release checklist added. |
| Off-host backup encryption/retention | NEEDS_HARDENING | Policy and handling are documented; an approved external backup destination is not part of this local portfolio target. |
| Public TLS/load balancer/object storage | OUT_OF_SCOPE | Deployment-specific infrastructure and public-production certification were not claimed. |
| Legacy backends/prototype surfaces | OUT_OF_SCOPE | `backend/`, `frontend/`, `mecprecision/`, and non-canonical prototype UI remain historical/legacy, not the Phase 6 runtime. |
| AI/OCR/chatbot/n8n/payments/microservices | OUT_OF_SCOPE | No integration or new product surface was introduced. |

No `BLOCKED` item remains for the authorized portfolio production-like Phase 6D
target.

## Production settings evidence

The running container reported only non-sensitive facts:

- `DEBUG=False`;
- database engine `django.db.backends.postgresql`;
- cache backend `django.core.cache.backends.redis.RedisCache`;
- hosts `127.0.0.1, localhost`, empty CORS, explicit loopback CSRF origin;
- secure session/CSRF cookies and one-year HSTS configuration;
- compressed manifest static storage;
- local staging used `SECURE_SSL_REDIRECT=False` because the documented gateway
  is loopback HTTP. Public HTTPS termination was not simulated or certified.

Focused configuration tests reject SQLite, incomplete PostgreSQL URLs,
non-Redis/incomplete Redis URLs, missing or wildcard hosts, non-empty production
CORS, wildcard CSRF origins, and the `CHANGE_ME` secret placeholder.

## Container, startup, and static runtime evidence

- Static and Django images were built from the current checkout. A Docker
  BuildKit issue caused by parallel builds in the Unicode workspace failed
  closed; the helper now builds sequentially.
- Django ran as `appuser`, read-only, healthy on `127.0.0.1:8001 -> 8000`.
- The static gateway ran as UID `101`, read-only, healthy on
  `127.0.0.1:8443 -> 8080`.
- PostgreSQL and Redis had no published host ports.
- The gateway returned 200 for `/` and `/api/v1/phase6/ready/`, served security
  headers, and proxied only to Django.
- A build-time `django-test.log` was found during artifact inspection. The
  Dockerfile was repaired to delete build logs, the backend image was rebuilt,
  and the final backend/frontend scans each found zero forbidden env, SQLite,
  database, dump, log, or production-sourcemap files.
- The startup helper always performs current-source builds, bounded dependency
  waits, migration and migration-consistency checks, then starts the runtime.
- A manual Compose recreation without the documented port override was refused
  by Docker because unrelated port 8000 was already allocated. No takeover
  occurred; recovery with explicit 8001/8443 passed. Operators must use the
  Phase 6D helper.

## Staging-like validation

- PostgreSQL, Redis, Django and static gateway: healthy.
- Django liveness on 8001 and gateway readiness on 8443: HTTP 200.
- Production frontend root on 8443: HTTP 200.
- Production Django `check`: zero issues.
- Production `migrate --check`: pass; `showmigrations` reported zero unapplied.
- Idempotent fictional fixture: three `.invalid` users and the bounded fictional
  customer/material/part were ready; no password/token was printed or persisted.
- Browser UAT through the production-static gateway:
  `PHASE6C_OWNER_UAT_PASS accessible_names=pass focus=BUTTON layouts=4 session_boundary=pass roles=pass`.
- That smoke covered authentication, canonical selectors/workspaces, Sales,
  Manager and Admin boundaries, Manager audit access, accessible audit controls,
  memory-session loss on hard refresh, and absence of cross-role mutable state.
- The full Phase 6B mutation chain was not rerun because Phase 6B already passed
  and Phase 6D required a bounded smoke, not duplicate append-only records.

## Backup and restore evidence

`Invoke-Phase6DBackupRestoreDrill.ps1` operated only on the Phase 6 PostgreSQL
container. It created an ignored custom-format dump, restored into a new
timestamped database in the Phase 6-owned cluster, verified 61 public tables and
an exact source/restored `django_migrations` fingerprint match, then force-dropped
only that temporary restore database. The source database and unrelated stacks
were never restore targets. Credentials did not appear in commands or reports.

The local dump is audit-sensitive even though data is fictional. It remains
ignored under `.phase6/`; it must be encrypted for off-host storage and expired
under an Owner-approved retention policy. Redis is disposable and is rebuilt,
not restored.

## Failure and recovery evidence

| Scenario | Evidence | Result |
|---|---|---|
| PostgreSQL unavailable | Phase 6 PostgreSQL stopped; readiness returned 503; service recovered healthy; readiness returned 200. | PASS |
| Redis unavailable | Phase 6 Redis stopped; readiness returned 503; service recovered healthy; readiness returned 200. | PASS |
| Invalid production config | Subprocess import matrix rejected invalid secret/database/cache/host/origin contracts. | PASS |
| Failed readiness | Public response remained sanitized as `not_ready`, without dependency details. | PASS |
| Migration mismatch | Startup and live runtime both ran `migrate --check`; zero unapplied migrations. No artificial corruption was introduced. | PASS |
| Port conflict | A controlled loopback listener caused the helper to exit with `port_collision` before Docker mutation. | PASS |
| Stale image | Startup uses sequential `build --pull` for current Django and frontend source. | PASS |
| Bounded restart | Explicit dependency recovery and Django image recreation returned all healthchecks to healthy. | PASS |
| Cleanup with profile | Initial stop exposed a profile-container omission; helper was repaired to include `--profile phase6d`; final cleanup removed all Phase 6 containers/network and retained volumes. | PASS |

## Security and release checks

- Scoped high-risk secret pattern scan: zero matching files.
- Final image forbidden-artifact scans: zero files in both images.
- No real PII or credentials were added. Fixture identities use `.invalid` and
  all business data is explicitly fictional.
- Browser bearer tokens remain memory-only; frontend regression tests prohibit
  local/session storage and logging.
- Exact permissions, lifecycle checks, canonical data contract, append-only
  audit/timeline evidence, and legacy MVP write blocking remain covered by
  focused tests.
- No wildcard production host/origin or permissive production CORS exists.
- No actual env value, database credential, Redis password, metrics token,
  browser bearer token, or idempotency key appears in this report.

## Regression results

Frontend:

- Phase 5A: 12 passed.
- Phase 5B: 18 passed.
- Phase 5C: 34 passed.
- Phase 5D: 22 passed.
- Phase 5E: 38 passed.
- Phase 6A: 5 passed.
- Phase 6B: 8 passed.
- Phase 6C: 5 passed.
- Phase 6D: 10 passed.
- Full frontend suite: 142 passed, 0 failed.
- TypeScript full and Phase 5A typechecks: passed.
- Vite production build: passed, 25 modules transformed.
- Phase 6A and Phase 6D Oxfmt checks: passed.

Backend and operations:

- Django test-settings check: zero issues.
- Migration generation consistency: no changes detected.
- Focused canonical/legacy-boundary/config/fixture/Phase 6D suite: 86 passed,
  8 skipped (conditional legacy artifacts).
- Final Phase 6A/6D configuration suite: 15 passed.
- Full backend pytest: 242 passed, 151 skipped, 0 failed.
- Production container Django check and migration consistency: passed.
- Ruff lint/format for touched Python: passed (pre-existing wildcard-import
  suppression is ignored only for the repository's current Ruff selection).
- PowerShell parser: zero errors for every Phase 6 helper.
- Phase 6D Compose profile rendering: passed.
- `git diff --check`: passed; line-ending conversion warnings only.
- Staged file count: zero.

No legacy test failure was masked. The 151 skips are existing conditional
legacy-artifact coverage, not Phase 6D failures.

## Files changed for Phase 6D

- `.github/workflows/ci.yml`
- `Dockerfile`
- `Dockerfile.phase6-frontend`
- `README.md`
- `docker-compose.phase6.yml`
- `docker/phase6/nginx.conf`
- `django_backend/config/settings/production.py`
- `django_backend/apps/core/tests/test_phase6a_configuration.py`
- `django_backend/apps/core/tests/test_phase6d_release_readiness.py`
- `figma_make_frontend/package.json`
- `scripts/phase6/Start-Phase6D.ps1`
- `scripts/phase6/Invoke-Phase6DBackupRestoreDrill.ps1`
- `scripts/phase6/Stop-Phase6.ps1`
- `docs/phase6/LOCAL_FULL_STACK.md`
- `docs/phase6/OPERATIONS.md`
- `docs/phase6/BACKUP_RESTORE.md`
- `docs/phase6/RELEASE_CHECKLIST.md`
- `PHASE_6D_STAGING_OPERATIONS_RELEASE_READINESS_REPORT.md`

The worktree already contained uncommitted Phase 5/6 changes. Those were
preserved and are not attributed to Phase 6D here.

## Final cleanup and limitations

The final approved stop helper removed every Phase 6 container and its private
network. Ports 8001 and 8443 were closed. The named PostgreSQL/media volumes were
preserved. `mecprecision-vietnam-web-1` retained container ID prefix
`dfd724919eb2`, image `mecprecision-vietnam:prod-local`, healthy state, restart
count 0, and port 8000 publication.

Remaining non-blocking limitations are remote CI evidence, an approved encrypted
off-host backup/retention system, and deployment-specific public TLS/load
balancer/object-storage validation. These do not block the explicitly scoped
local portfolio production-like demo and are not public-production certification.

## Final verdict

PASS_PHASE_6D_STAGING_OPERATIONS_RELEASE_READINESS
