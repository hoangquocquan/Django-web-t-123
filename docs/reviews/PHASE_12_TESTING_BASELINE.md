# Phase 12 Testing Baseline

## Existing Tests

The repository contains tests at two levels:

| Location | Purpose |
| --- | --- |
| `tests/` | Migration governance, evidence, archive and top-level regression tests |
| `django_backend/tests/` | Django project-level migration and compatibility tests |
| `django_backend/apps/*/tests/` | App-level ORM, service and API tests |
| `backend/tests/` | Legacy custom backend behavior tests |

## Current Automated Results

Latest Phase 12 validation:

| Command | Result |
| --- | --- |
| `pytest tests/test_phase12_system_baseline.py` | PASS |
| `pytest` | PASS |
| `powershell -ExecutionPolicy Bypass -File scripts/run_migration_test.ps1` | PASS |

The repository-level pytest suite collected 97 tests before the Phase 12 test
was added. The migration test script also runs Django system check plus app
regression tests and reported `MIGRATION TEST PASSED`.

## Migration Tests

Migration tests cover:

- database routing safety
- unmanaged/read-only ORM models
- API compatibility
- API hardening
- Phase 10 database cutover readiness
- Phase 11 legacy API decommission governance
- Phase 11.2 database archive integrity

## Coverage Status

Formal line coverage is not yet measured in this baseline. Current confidence
comes from targeted regression tests, query pattern tests and phase-specific
governance tests.

## Known Missing Tests

| Missing area | Recommendation |
| --- | --- |
| Browser/UI smoke tests | Add Playwright or equivalent for critical flows |
| Production auth flow | Add after auth cutover design is approved |
| Full frontend-to-Django contract tests | Add before frontend API cutover |
| Load/performance tests | Add in performance phase |
| Secret scanning | Add in security phase |
| Backup restore drill | Add after archive retention policy is approved |

## Testing Baseline Decision

The current test suite is strong for migration governance and Django read/API
compatibility. Next phases should add coverage reporting, browser tests,
security scans and performance benchmarks.
