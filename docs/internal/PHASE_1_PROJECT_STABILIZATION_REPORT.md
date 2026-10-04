# Phase 1 Project Stabilization Report

## Verdict

`PASS_WITH_NOTES`

The canonical Django and React/Vite paths now start, validate, and build from a
clean-clone configuration. The note is limited to historical Phase 10/11 tests
that require an untracked legacy SQLite artifact; that artifact was not created
or copied into the repository to hide the dependency.

## Repository baseline

- Task: `DJANGO-PHASE-1-PROJECT-STABILIZATION-V1`
- Branch: `codex/demo-database-validation`
- Commit before changes: `df14dc510fee53189bfd70fe0d9aa9fb2de7c7d0`
- Working tree before changes: clean (`git status --porcelain=v1` returned no
  entries).
- No applicable root `AGENTS.md` was present. The nested
  `figma_make_frontend/AGENTS.md` was read before frontend validation.

## Inventory and decisions

- Canonical backend: `django_backend/`; CLI entrypoint
  `django_backend/manage.py`; WSGI entrypoint `config.wsgi:application`.
- Canonical frontend: `figma_make_frontend/`; Vite/React entrypoint
  `src/main.tsx`; package manager pnpm using `pnpm-lock.yaml`.
- Toolchain evidence: Python 3.12 in Docker and workflows; Node 22 and pnpm
  10.34.3 in `figma_make_frontend/.mise.toml`.
- Legacy/prototype areas retained without deletion: `backend/`, `frontend/`,
  and `mecprecision/`.
- Active backend manifests: `django_backend/requirements.txt` and
  `django_backend/requirements-prod.txt`.
- Active frontend manifests: `figma_make_frontend/package.json` and
  `figma_make_frontend/pnpm-lock.yaml`.
- Workflows audited: `.github/workflows/ci.yml`, `aws-lab-ci.yml`, and
  `test_pipeline.yml`.
- Deployment runtime audited: root `Dockerfile` uses Gunicorn and production
  requirements; production Django settings insert WhiteNoise; Compose defines
  Django, PostgreSQL 16, Redis 7, and n8n.
- Custom application admin is `/admin/`; Django technical admin is
  `/django-admin/`.

## Problems and root causes

1. The root README described the retired `backend/app.py`, static `frontend/`,
   a personal Windows path, legacy SQLite setup/seed commands, and demo
   credentials as the default application. Root cause: documentation had not
   followed the completed Django migration and new Vite frontend.
2. Main CI compiled and tested the retired backend and static frontend. Two
   specialist workflows also installed `backend/requirements.txt`. Root cause:
   workflow paths predated canonical ownership.
3. Django always registered a `legacy` SQLite alias pointing to
   `backend/database/mecprecision.sqlite`. The file is ignored and absent in a
   fresh clone. Root cause: the compatibility fallback encoded a local artifact
   as an implicit runtime dependency.
4. The root `.env.example` documented only legacy `MEC_*` variables and an
   author-machine database path. Root cause: it belonged to the retired backend.
5. Legacy compatibility tests failed during fixture setup when the ignored
   SQLite source was absent. Root cause: fixture setup assumed the optional
   artifact existed instead of declaring the test unavailable.

## Changes made

- Replaced the root README with current Django/React setup, commands, routes,
  Docker requirements, and explicit legacy/prototype status.
- Rebuilt the main CI around `django_backend/` and `figma_make_frontend/`:
  Django check, migration drift check, fresh-clone-safe Django tests, locked
  pnpm install, and frontend build.
- Removed all workflow installs of the legacy backend requirements file while
  retaining the existing specialist workflow checks.
- Made legacy SQLite compatibility opt-in with
  `LEGACY_DATABASE_ENABLED=true` plus an explicit `LEGACY_DATABASE_URL`.
  Enabling it without a URL fails closed. Default settings register no legacy
  alias and cannot silently create an ignored database.
- Kept legacy test coverage possible by registering a disposable read-only
  alias in the test fixture. Tests are explicitly skipped if the source
  compatibility artifact is unavailable; no fake database is generated.
- Standardized root and Django `.env.example` files with placeholders only.
- Added a startup/settings regression test proving legacy DB is disabled by
  default.

Changed files:

- `.env.example`
- `.github/workflows/aws-lab-ci.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/test_pipeline.yml`
- `README.md`
- `django_backend/.env.example`
- `django_backend/config/settings/base.py`
- `django_backend/config/settings/test.py`
- `django_backend/conftest.py`
- `django_backend/tests/test_project_stabilization.py`
- `PHASE_1_PROJECT_STABILIZATION_REPORT.md`

## Verification

Commands and results:

- `python manage.py check` with development settings: PASS, 0 issues.
- `DJANGO_SETTINGS_MODULE=config.settings.test python manage.py check`: PASS,
  0 issues.
- `python manage.py makemigrations --check --dry-run`: PASS, no changes.
- `python -m pytest apps tests/test_project_stabilization.py -q`: PASS,
  12 passed and 104 skipped because optional legacy data was absent.
- Targeted startup/database/health run: PASS, 4 passed and 9 legacy-dependent
  tests skipped.
- Full `python -m pytest -q`: 99 passed, 136 skipped, 4 failed. The four failures
  are historical Phase 10/11 readiness tests that directly require the absent
  `backend/database/mecprecision.sqlite`; they are not in the fresh-clone CI
  gate.
- `pnpm install --frozen-lockfile`: PASS using the existing lockfile/cache. pnpm
  emitted a non-fatal registry metadata fetch warning in the restricted
  environment.
- `pnpm build`: PASS with Vite 8.0.5 (16 modules transformed).
- Parse every `.github/workflows/*.yml` with PyYAML: PASS.
- `docker compose config --quiet` with validation-only required values: PASS.
  Docker emitted a host config permission warning, but Compose validation exited
  0.
- Active-path search for `backend/requirements.txt`, `python backend/app.py`,
  and personal author paths: no stale default-path matches.
- `git diff --check`: PASS; only Git's existing LF-to-CRLF notices were emitted.
- Changed-file scan for `models.py` or `/migrations/`: no matches.

## Unverified or intentionally excluded

- Legacy data-dependent compatibility behavior was not executed because the
  SQLite source is not tracked and was absent. Supplying it remains an explicit
  opt-in operation.
- Containers were not started, migrations were not applied to PostgreSQL, and
  no live Redis/n8n/Ollama service was contacted. Compose syntax was validated.
- No frontend test or lint was run because `package.json` defines neither
  script. The production build is the available frontend gate.
- GitHub-hosted Actions were not executed locally; their YAML and underlying
  commands were validated where possible.

## Git state snapshot

`git diff --stat`:

```text
 .env.example                           |  50 ++-
 .github/workflows/aws-lab-ci.yml       |   2 +-
 .github/workflows/ci.yml               |  76 ++--
 .github/workflows/test_pipeline.yml    |   2 +-
 README.md                              | 676 +++++----------------------------
 django_backend/.env.example            |   1 +
 django_backend/config/settings/base.py |  28 +-
 django_backend/config/settings/test.py |   1 -
 django_backend/conftest.py             |  37 +-
 9 files changed, 227 insertions(+), 646 deletions(-)
```

Final `git status --short` (including untracked task artifacts):

```text
 M .env.example
 M .github/workflows/aws-lab-ci.yml
 M .github/workflows/ci.yml
 M .github/workflows/test_pipeline.yml
 M README.md
 M django_backend/.env.example
 M django_backend/config/settings/base.py
 M django_backend/config/settings/test.py
 M django_backend/conftest.py
?? PHASE_1_PROJECT_STABILIZATION_REPORT.md
?? django_backend/tests/test_project_stabilization.py
```

## Scope and safety confirmations

- No business model was changed.
- No migration was created or modified.
- No seed, data mutation, or production database operation was run.
- No legacy directory was deleted.
- Validation, authentication, authorization, and fail-closed behavior were not
  weakened.
- No real secret, credential, or personal data was added.
- No commit, push, pull request, deployment, or production action was performed.

## Phase 2 recommendations (not performed)

1. Classify and mark the remaining historical Phase 10/11 tests with an
   explicit legacy-artifact marker so full-suite results distinguish current
   Django regressions from archive validation.
2. Complete migration of remaining read paths that still use repository alias
   `legacy`, then remove the compatibility alias and fixture in a separately
   reviewed task.
3. Add a frontend lint/type-check/test script if the team wants gates beyond the
   current Vite production build.
4. Run the production-like Compose stack with disposable PostgreSQL/Redis
   volumes in a dedicated infrastructure validation phase.
