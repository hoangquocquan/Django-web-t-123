# Phase 6A Full-Stack Foundation Implementation Report

## Final verdict

BLOCKED_PHASE_6A

The Phase 6A source foundation, static validation, focused tests, CI wiring, and local operator documentation were implemented. The final production-like live validation remains blocked because the local Docker engine became unresponsive during isolated stack startup and cleanup verification. I am not marking this ready for review because PostgreSQL-backed runtime migration/smoke evidence could not be completed.

## Baseline gate evidence

| Gate | Result |
| --- | --- |
| Repository root | `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO` |
| Remote | `https://github.com/hoangquocquan/Django-web-t-123.git` |
| Branch | `codex/demo-database-validation` |
| Required baseline HEAD | `01f15037e64d6c565e8444dc99eee6c9eb7c37f4` |
| Required subject | `phase5e: repair progress reconciliation evidence matching` |
| Initial staged state | Empty |
| Initial status | `?? PHASE_6_SCOPE_DISCOVERY_AND_RELEASE_PLAN.md` |
| Release-plan verdict | `READY_FOR_PHASE_6A` |
| Plan handling | `PHASE_6_SCOPE_DISCOVERY_AND_RELEASE_PLAN.md` was read for scope and not edited |

## Implemented scope

Phase 6A adds an isolated local full-stack foundation without reusing the repository's broader compose stack. The new stack is owned by a fixed project prefix, uses PostgreSQL and Redis without publishing their ports, publishes Django on loopback only, and routes the Vite frontend through a loopback-only `/api` proxy.

The backend now has Phase 6A liveness/readiness probes, stricter production/development configuration validation, a shared legacy-record write boundary, and inactive-role permission denial that applies to foundation/legacy route checks.

The frontend now has a Phase 6A Vite server configuration module with tests, no direct API-origin override for browser runtime calls, and local env examples that contain no secrets.

## Changed paths

- `.github/workflows/ci.yml`
- `.gitignore`
- `.env.phase6.example`
- `README.md`
- `PHASE_6A_FULL_STACK_FOUNDATION_IMPLEMENTATION_REPORT.md`
- `docker-compose.phase6.yml`
- `docs/phase6/LOCAL_FULL_STACK.md`
- `scripts/phase6/Initialize-Phase6Environment.ps1`
- `scripts/phase6/Start-Phase6.ps1`
- `scripts/phase6/Stop-Phase6.ps1`
- `django_backend/apps/common/legacy_write_boundary.py`
- `django_backend/apps/business_core/services.py`
- `django_backend/apps/transaction_domain/services.py`
- `django_backend/apps/sales/services/sales_platform_service.py`
- `django_backend/apps/foundation/services.py`
- `django_backend/apps/core/views.py`
- `django_backend/apps/core/urls.py`
- `django_backend/config/settings/development.py`
- `django_backend/config/settings/production.py`
- `django_backend/apps/api/tests/test_phase6a_legacy_write_boundary.py`
- `django_backend/apps/core/tests/test_phase6a_configuration.py`
- `figma_make_frontend/.gitignore`
- `figma_make_frontend/.env.example`
- `figma_make_frontend/package.json`
- `figma_make_frontend/vite.config.ts`
- `figma_make_frontend/phase6.config.ts`
- `figma_make_frontend/phase6.config.test.ts`

## Runtime ownership and isolation

`docker-compose.phase6.yml` defines only Phase 6A resources:

- Compose project name: `django-web-t-123-phase6`
- Containers: `django-web-t-123-phase6-postgres`, `django-web-t-123-phase6-redis`, `django-web-t-123-phase6-django`
- Network: `django-web-t-123-phase6-internal`
- Volumes: `django-web-t-123-phase6-postgres-data`, `django-web-t-123-phase6-media`
- Published ports: Django only, `127.0.0.1:${PHASE6_DJANGO_PORT:-8000}:8000`
- PostgreSQL/Redis published ports: none
- External networks/volumes: none

`Start-Phase6.ps1` validates the required configuration names, checks only the configured Phase 6A ports, starts dependencies with bounded waits, runs migrations plus `migrate --check`, starts Django, starts Vite, and checks the live/ready endpoints plus representative frontend routes through Vite. Startup writes a sanitized `.phase6/logs/startup-result.json`.

`Stop-Phase6.ps1` targets only the Phase 6A compose project and optional owned volumes. It verifies the recorded Vite process identity before stopping it.

## Frontend routing contract

`figma_make_frontend/phase6.config.ts` rejects malformed, remote, credentialed, path-bearing, portless, or non-HTTP Django origins. It binds Vite to `127.0.0.1`, uses strict port behavior, and proxies only `/api` to the configured local Django origin.

Existing frontend API clients continue using root-relative paths such as `/api/v1/canonical/` and `/api/v1/foundation/auth/`.

## Legacy write boundary

Discovery found routed legacy mutation surfaces for:

- Business/admin customer `PUT`
- Business/admin product `PUT`
- Orders/workflows `PUT` and workflow `POST`
- Admin order/workflow aliases
- Sales legacy quotation create/recalculate/approve/handoff service paths

No routed non-canonical material mutation, routed non-canonical RFQ mutation, or routed legacy delete endpoint was found during discovery.

Implemented protection:

- New shared guard: `django_backend/apps/common/legacy_write_boundary.py`
- Business customer/product legacy creates force `data_contract="LEGACY"`
- Business customer/product legacy updates reject non-LEGACY records
- Transaction order legacy creates force `data_contract="LEGACY"`
- Transaction order update keeps the existing Phase 4D MVP_V1 guard semantics through the shared guard
- Sales legacy quotation create paths force LEGACY records/lines
- Sales legacy quotation recalculate/approve/handoff reject MVP_V1/non-LEGACY quotations
- Foundation permission checks reject inactive roles

## Configuration hardening

Production settings now fail closed for:

- Missing PostgreSQL database configuration
- Missing Redis cache/session configuration
- Wildcard, schemed, path-bearing, whitespace, or empty `ALLOWED_HOSTS`
- Non-empty `CORS_ALLOWED_ORIGINS`
- Malformed CSRF trusted origins

Development settings now validate loopback HTTP CORS origins with explicit ports.

Production PostgreSQL options include bounded connect timeout configuration through `DATABASE_CONNECT_TIMEOUT_SECONDS`.

## Validation evidence

Commands completed successfully:

- `pnpm run test:phase6a` - passed 4 tests
- `pnpm run typecheck` - passed
- `pnpm run typecheck:phase5a` - passed
- Phase 5A focused frontend tests - passed 12
- Phase 5B focused frontend tests - passed 18
- Phase 5C focused frontend tests - passed 30
- Phase 5D focused frontend tests - passed 22
- Phase 5E focused frontend tests - passed 38
- `pnpm run test` - passed 124 tests
- `pnpm run build` - passed
- `pnpm run format:check:phase6a` - passed
- `python -m pytest -q apps/core/tests/test_phase6a_configuration.py apps/api/tests/test_phase6a_legacy_write_boundary.py` - passed 17
- `python -m pytest -q apps/api/tests/test_phase4d_order_progress_commands.py` - passed 11, skipped 4
- `python manage.py makemigrations --check --dry-run --settings=config.settings.test` - no changes detected
- `python manage.py check --settings=config.settings.test` - no issues
- Full backend `python -m pytest -q` - passed 232, skipped 151
- Final combined backend validation - passed 28, skipped 4, check clean, migrations clean
- PowerShell parser check for `scripts/phase6/*.ps1` - passed
- `docker compose -p django-web-t-123-phase6 --env-file .env.phase6.example -f docker-compose.phase6.yml config --quiet` - passed, with a Docker config access warning but exit code 0
- CI YAML parse check - passed
- `git diff --check` - exit code 0, CRLF warnings only

Known validation corrections during implementation:

- Phase 6A backend fixture was corrected to avoid permission uniqueness collisions.
- Frontend format check was split into a Phase 6A-specific command after the existing formatter script mishandled passthrough args on Windows.
- `Start-Phase6.ps1` cleanup behavior was corrected so a timeout after compose mutation invokes cleanup logic.

## Live validation blocker

Live PostgreSQL/runtime validation did not complete.

Evidence:

- Phase 6A ports `8000` and `8443` were checked before startup and were empty.
- `.env.phase6` was created by `Initialize-Phase6Environment.ps1`; generated values were not displayed, read, hashed, or committed.
- First startup attempt failed closed because Docker API access was unavailable.
- Docker Desktop was started through the existing installed application.
- A subsequent escalated startup attempt reached the bounded dependency/build/migration path but timed out with `timeout: Phase 6A startup failed closed`.
- Subsequent targeted compose and Docker status operations against the exact Phase 6A project/engine hung, indicating the local Docker engine was unresponsive.
- Final Phase 6A port checks showed ports `8000` and `8443` empty.

Blocked items:

- Real PostgreSQL migration smoke inside the Phase 6A compose stack
- Runtime `/api/v1/phase6/live/` and `/api/v1/phase6/ready/` smoke from the running Django container
- Browser-equivalent smoke through live Vite
- Confirmed Docker resource cleanup state

Cleanup note: `Stop-Phase6.ps1 -RemoveOwnedVolumes` was attempted against the exact Phase 6A compose project, but Docker operations timed out. No broad Docker cleanup or unrelated resource inspection was performed.

## Credential handling

No credential values from `.env.phase6` were read, printed, hashed, logged intentionally, staged, or committed. The only hashed env file is `.env.phase6.example`, which contains placeholder values only.

## Unrelated resource handling

No unrelated stacks or external project resources were started, modified, cleaned, or inspected beyond repository source discovery. The existing broader compose stack was not used for Phase 6A. No AI FACTORY, n8n, Zalo, 9Router, or Codex Bridge resources were modified.

## SHA256 evidence

| SHA256 | Path |
| --- | --- |
| `45a8256af2f69ddadfe9608eb815ce07917d422140f47ded4e270ac813412cf9` | `.github/workflows/ci.yml` |
| `2a9022c60fd0353e80d376ba3c32b0aae4738275a5dbaab0e1abeac05a87a078` | `.gitignore` |
| `3df41f8578ae5c88b4c5591427d16b75f2ab1cda0a4d77b8558be29789b44a39` | `.env.phase6.example` |
| `40f7f58c0c22a8a71a784a9bbccddde15f83990755bad38468ac2d6610ae74fa` | `README.md` |
| `3c0efb1b184d42cbf5f59a15deffba13b0bec6392de185180745d11f7fe55181` | `docker-compose.phase6.yml` |
| `73ab5d5230e6c08e2e47d40ac942a889d21e78ef49f1076e6531e2f453176665` | `docs/phase6/LOCAL_FULL_STACK.md` |
| `7b6a461042527554f660a8e636f4072c6b331f88c8234e687bcbd987a781ff30` | `scripts/phase6/Initialize-Phase6Environment.ps1` |
| `f124f2b62a39e832bdfe259cd513a581b8511ce18435de2326c2ac1ec873398f` | `scripts/phase6/Start-Phase6.ps1` |
| `d5513ee380c9adf4e22ac6aa0a1d59ed5201b38bfe989c06f87b8b4e34f6ee8c` | `scripts/phase6/Stop-Phase6.ps1` |
| `f05fed1c333dd1d34ad5eb1958ad2ad111fe0f0417013e9c2a9a07093b0b4c38` | `django_backend/apps/common/legacy_write_boundary.py` |
| `85120d8dc69cea22447a9fdf13eadce5d9cc129395d37a3eb9a49d706606c76e` | `django_backend/apps/business_core/services.py` |
| `1180beb7f00ebec096b6880105eb5e1da41a930e6183783860699b305acd90af` | `django_backend/apps/transaction_domain/services.py` |
| `06c65f6fdf09f694b3c704af830432cdbd3823cdaed77799c0330ae922db035f` | `django_backend/apps/sales/services/sales_platform_service.py` |
| `325c0c60d955285f61115c283b426b127eddcf793a20a5d96d4c81d277992b87` | `django_backend/apps/foundation/services.py` |
| `410207e292564a6048c0bc1942115cb462a0eee93ccf826984da720c4cc0c37c` | `django_backend/apps/core/views.py` |
| `b58c88ec41016a9682e6b16e2b8f10a664d4662d1906f3ded1ca994226717ff1` | `django_backend/apps/core/urls.py` |
| `eaf6ecbd9dd983cc464d87fbf468368da4d4528a5fc6c5b6bf3d1208b452be12` | `django_backend/config/settings/development.py` |
| `ad4324e70e8c30e85c8eff4f556c21f966442f43a618b674116d44b44e22f6e2` | `django_backend/config/settings/production.py` |
| `3b00ed9a46f89da6d61f7b53f1fa0fd67a4680facd0d827dba6b81379056145b` | `django_backend/apps/api/tests/test_phase6a_legacy_write_boundary.py` |
| `bbbc60c7c973c5a317e852d7905b1b0615cb8083d560abd46111e711e031911c` | `django_backend/apps/core/tests/test_phase6a_configuration.py` |
| `32100ff56dbbafd95bcf8279212e75b3477f93c240f9f7f06f0c2f672ff1f4ed` | `figma_make_frontend/.gitignore` |
| `32f6f19a06cca0c053cea4c9488533ceb11389e6a769af6f530e6e5894038c35` | `figma_make_frontend/.env.example` |
| `89909ac675aae312559e888df10b967e6b5d4b9fc199c056e22432e5dbe4be1e` | `figma_make_frontend/package.json` |
| `deea0044d16e75f827e4a39530271da86846926be2c4a89c350b9063896d23d5` | `figma_make_frontend/vite.config.ts` |
| `7742fff4b366592a0065c7778b5a2fbe8604a2c0f12762f04c3c5f87a3599ef2` | `figma_make_frontend/phase6.config.ts` |
| `01952a5caf1fd02946fbce4393870b51aebd7886e3999d2e1131462ac9245111` | `figma_make_frontend/phase6.config.test.ts` |

## Remaining risks

- Docker engine responsiveness must be restored before final review.
- Phase 6A compose cleanup state cannot be independently verified while Docker commands hang.
- The runtime PostgreSQL migration smoke and browser-equivalent smoke must be rerun successfully before changing the verdict to ready.

## Commit state

No files were staged or committed by this implementation pass.
