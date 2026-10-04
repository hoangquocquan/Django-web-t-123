# Phase 1 Full Test Closure Report

## Verdict

`PASS`

The default fresh-clone lane now runs the full collected backend suite with
`0 failed` and `0 errors`. Tests requiring the Owner's legacy SQLite artifact
remain collected, are classified with `legacy_artifact`, and are skipped only
when explicit read-only legacy configuration is unavailable.

## Repository baseline

- Task: `DJANGO-PHASE-1-FULL-TEST-CLOSURE-V1`
- Branch: `codex/demo-database-validation`
- Base commit: `df14dc510fee53189bfd70fe0d9aa9fb2de7c7d0`
- Working tree before this task contained the valid, uncommitted Phase 1 changes:
  `.env.example`, all three workflow files, `README.md`,
  `django_backend/.env.example`, Django base/test settings, `conftest.py`, the
  stabilization report, and `test_project_stabilization.py`.
- No root `AGENTS.md` exists. The applicable nested frontend instructions had
  already been read and were followed for the repeated build.

## The four former failures

1. `tests/test_phase10_dry_run_gate.py::test_dry_run_gate_blocks_missing_target_database`
   - Purpose: prove a missing PostgreSQL dry-run target remains blocked and no
     production operation occurs, while reporting a 27-table legacy snapshot.
   - Direct dependency: `evaluate_dry_run()` called `snapshot_database()`, which
     opened `backend/database/mecprecision.sqlite` read-only.
   - Root cause: the test did not use `legacy_db`; therefore its explicit
     27-table assertion bypassed the fixture-level missing-artifact skip.
   - Classification: legacy migration-readiness compatibility test. It requires
     a real artifact and cannot be truthfully replaced by a generated fixture.
2. `tests/test_phase10_dry_run_gate.py::test_dry_run_gate_rejects_production_marker_even_when_dryrun_exists`
   - Purpose: reject PostgreSQL database names containing a production marker.
   - Direct dependency: the same unconditional snapshot call ran before URL
     validation returned its result.
   - Root cause: no `legacy_db` fixture and no configurable SQLite argument.
   - Classification: legacy Phase 10 tooling integration test. Although the URL
     rule itself is pure, this test calls an integration function whose contract
     includes the real snapshot.
3. `tests/test_phase10_readiness_snapshot.py::test_phase10_snapshot_reads_legacy_database_without_mutation`
   - Purpose: inspect all expected tables and prove the source SQLite size is
     unchanged.
   - Direct dependency: `snapshot_database()` directly opened the default file.
   - Root cause: the test directly used the script helper instead of the legacy
     fixture, so the existing skip never ran.
   - Classification: artifact-only legacy verification; a fake database would
     invalidate the table/count and immutability evidence.
4. `tests/test_phase11_legacy_shutdown_readiness.py::test_phase11_can_be_ready_for_manual_review_when_all_gates_are_mocked`
   - Purpose: prove Phase 11 can reach manual-review readiness only when every
     flag, decision marker, and rollback asset exists.
   - Direct dependency: `inspect_legacy_assets()` checked
     `LEGACY_ASSETS["legacy_database"]`, the absent SQLite file.
   - Root cause: the test mocked operational flags and decision report but not
     the required external database asset; it also did not use `legacy_db`.
   - Classification: legacy shutdown/archive readiness test. It must use a real
     Owner-provided artifact path.

## Legacy classification and two test lanes

- Registered marker: `legacy_artifact` in `django_backend/pytest.ini`.
- Tests declaring `legacy_db` or `legacy_artifact_path` are automatically and
  narrowly classified during collection. The four direct callers above are
  explicitly decorated.
- A test is runnable only when both conditions hold:
  `LEGACY_DATABASE_ENABLED=true`, and `LEGACY_DATABASE_URL` is a `file:` URI
  containing `mode=ro` that resolves to an existing file.
- Otherwise it is skipped with exactly:
  `legacy SQLite artifact is not available in a fresh clone`.
- The legacy fixture copies only the explicitly supplied real artifact into a
  temporary test directory and opens that copy read-only. It never generates,
  seeds, commits, or silently substitutes a database.
- `evaluate_dry_run()` now accepts a configurable legacy path, and its existing
  CLI `--sqlite-database` option is honored in evaluation mode as well as
  execution mode.

Default full lane:

```text
cd django_backend
python -m pytest -q
```

Optional Owner-provided legacy lane:

```powershell
$env:LEGACY_DATABASE_ENABLED = "true"
$env:LEGACY_DATABASE_URL = "file:C:/path/to/existing/mecprecision.sqlite?mode=ro"
python -m pytest -m legacy_artifact -q
```

## Files changed by this closure task

- `.github/workflows/ci.yml`
- `README.md`
- `django_backend/conftest.py`
- `django_backend/pytest.ini`
- `django_backend/tests/test_phase10_dry_run_gate.py`
- `django_backend/tests/test_phase10_readiness_snapshot.py`
- `django_backend/tests/test_phase11_legacy_shutdown_readiness.py`
- `scripts/phase10_dry_run_migration.py`
- `PHASE_1_FULL_TEST_CLOSURE_REPORT.md`

All valid files from the prior stabilization task remain preserved.

## Verification results

- Initial focused reproduction with full tracebacks: exactly 4 collected and
  4 failed, matching the prior report.
- Focused four-test skip contract: `4 skipped`, `0 failed`, `0 errors`; each
  item reported the required fresh-clone reason.
- Marker collection contract: `140/239 tests collected`, with 99 non-legacy
  tests deselected for the optional lane.
- Optional lane without an artifact: `140 skipped, 99 deselected`, with the
  same explicit reason. Legacy test bodies were not claimed as verified.
- Django development system check: PASS, 0 issues.
- Django test-settings system check: PASS, 0 issues.
- Migration drift: PASS, `No changes detected`.
- Full backend test, `python -m pytest -q`: PASS — `99 passed, 140 skipped in
  1.47s`; `0 failed`, `0 errors`.
- Frontend locked install: PASS from existing lock/cache; pnpm emitted a
  non-fatal registry metadata warning in the restricted environment.
- Frontend production build: PASS with Vite 8.0.5; 16 modules transformed.
- All `.github/workflows/*.yml` parsed successfully with PyYAML.
- Main CI now runs the exact full command `python -m pytest -q`; it has no
  `--ignore`, `continue-on-error`, `|| true`, reduced test selection, or omitted
  test folder. Django system and migration checks remain present.
- `git diff --check`: PASS; only repository line-ending notices were emitted.
- Changed-path scan found no model, migration, seed, data, or SQLite file.
- `git status --short` contained no SQLite artifact.

## Skip classification

- Missing legacy SQLite artifact: **140**.
- Platform-specific skip: **0**.
- Optional dependency/service skip: **0**.
- Other reason: **0**.

The total rose from 136 to 140 only because the four previously failing tests
were correctly added to the same artifact-dependent lane. No current test was
blanket-skipped, ignored, deleted, or weakened.

## Current cumulative Git diff

`git diff --stat` (tracked changes from both Phase 1 tasks; untracked reports and
the new stabilization test are listed by status instead):

```text
 .env.example                                       |  50 +-
 .github/workflows/aws-lab-ci.yml                   |   2 +-
 .github/workflows/ci.yml                           |  76 ++-
 .github/workflows/test_pipeline.yml                |   2 +-
 README.md                                          | 681 +++------------------
 django_backend/.env.example                        |   1 +
 django_backend/config/settings/base.py             |  28 +-
 django_backend/config/settings/test.py             |   1 -
 django_backend/conftest.py                         |  85 ++-
 django_backend/pytest.ini                          |   2 +
 django_backend/tests/test_phase10_dry_run_gate.py  |  15 +-
 .../tests/test_phase10_readiness_snapshot.py       |   9 +-
 .../test_phase11_legacy_shutdown_readiness.py      |  13 +-
 scripts/phase10_dry_run_migration.py               |   6 +-
 14 files changed, 319 insertions(+), 652 deletions(-)
```

Final `git status --short`:

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
 M django_backend/pytest.ini
 M django_backend/tests/test_phase10_dry_run_gate.py
 M django_backend/tests/test_phase10_readiness_snapshot.py
 M django_backend/tests/test_phase11_legacy_shutdown_readiness.py
 M scripts/phase10_dry_run_migration.py
?? PHASE_1_FULL_TEST_CLOSURE_REPORT.md
?? PHASE_1_PROJECT_STABILIZATION_REPORT.md
?? django_backend/tests/test_project_stabilization.py
```

## Safety confirmations and phase conclusion

- No business behavior, production model, migration, seed, or data was changed.
- No test was deleted, assertion weakened, ignored, or hidden from full
  collection.
- No fake or copied-in legacy SQLite artifact was created or committed.
- No production database or service was contacted.
- No commit, push, pull request, deploy, or Phase 2 work was performed.

All Phase 1 full-test-closure acceptance criteria are satisfied. The repository
is eligible to begin Phase 2 when the Owner authorizes it.
