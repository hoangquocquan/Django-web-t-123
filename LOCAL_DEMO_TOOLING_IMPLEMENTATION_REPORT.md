# Local Demo Tooling Safe-Seed Implementation Report

Repository: https://github.com/hoangquocquan/Django-web-t-123

Base SHA: c41ee1ddee72951f891349b55777da31d6c952f5

Branch: feat/local-demo-tooling-safe-seed

## Exact changed files

- django_backend/apps/core/management/commands/ensure_local_ai_demo_user.py
- django_backend/apps/core/management/commands/seed_production_demo.py
- django_backend/apps/core/production_demo_seed/__init__.py
- django_backend/apps/core/production_demo_seed/ai_eval_cases.py
- django_backend/apps/core/production_demo_seed/generators.py
- django_backend/apps/core/production_demo_seed/historical.py
- django_backend/apps/core/production_demo_seed/lifecycle.py
- django_backend/apps/core/production_demo_seed/ownership.py
- django_backend/apps/core/production_demo_seed/profiles.py
- django_backend/apps/core/production_demo_seed/report.py
- django_backend/apps/core/production_demo_seed/safety.py
- django_backend/apps/core/production_demo_seed/validators.py
- django_backend/apps/core/tests/test_production_demo_seed.py
- django_backend/apps/core/tests/test_production_demo_safety.py
- LOCAL_DEMO_TOOLING_IMPLEMENTATION_REPORT.md

No migrations, frontend, AI Sales, Knowledge feature logic, LINE/n8n code, credentials, or runtime artifacts are included.

## Safety implementation

- Explicit environments only: DEV, TEST, STAGING, UAT.
- Missing/unknown/PRODUCTION environment fails closed; DEBUG is not used as an allow decision.
- Apply requires --apply, allowed environment, exact DEMO_TOOLING_DATABASE_ALLOWLIST identity, and PRODUCTION_DEMO_SEED_ALLOWED=true.
- Dry-run is the default and performs zero writes.
- Database identity checks engine, host, port, name, and normalized SQLite path. SQLite alone is never sufficient.
- Production-looking names/paths and unknown remote hosts are rejected.
- Seed data uses deterministic production_demo_v1 markers, stable pdv1-* keys, and reserved @production-demo.invalid identities.
- Demo-user command rejects real domains, existing non-demo collisions, role changes, wildcard permissions, and missing safety gates. Password is operator-supplied and never printed.
- TEST and SMALL are enabled; FULL is explicitly rejected.
- No broad delete/truncate/flush/reset/drop operation exists in the new package.
- No direct LINE, n8n, email, HTTP/provider, payment, delivery, or outbound-job call exists.
- Knowledge fixtures are synthetic and governance-compatible; no public/pilot publication or rollout switch is enabled.

## Permission profile

The seed reuses canonical Admin, Sales, and Manager role names for existing command-service compatibility, but assigns only profile-required permissions. No wildcard permission or superuser is created. Sensitive quotation/RFQ workflow permissions are exercised only by the synthetic lifecycle scenarios and are covered by the seed tests.

## Validation

- Production-demo seed tests: 16 passed
- Safety regression tests: 16 passed
- Django system check: PASS
- makemigrations --check --dry-run: PASS; no changes
- Python compile: PASS
- Feature Ruff: PASS
- git diff --check: PASS
- Secret/runtime scan: PASS; no secrets or runtime artifacts
- Isolated TEST dry-run/apply/re-apply: PASS; stable counts (12, 35, 20, 8)
- Isolated SMALL dry-run/apply/re-apply: PASS; stable counts (60, 300, 220, 100)
- PostgreSQL local smoke: not available in this workstation; required CI PostgreSQL smoke remains a delivery gate.

## Blockers

No feature-caused blocker remains. The isolated suite emits a pytest teardown warning on Windows in this environment, but all assertions pass and no repository artifact is retained. The feature remains DEV/TEST/STAGING/UAT-only and is never approved for production execution.

## Verdict

LOCAL DEMO TOOLING IMPLEMENTATION: PASS
PRODUCTION REFUSAL: PASS
DATABASE SAFETY: PASS
SYNTHETIC ONLY: PASS
USER PROTECTION: PASS
LEAST PRIVILEGE: PASS
IDEMPOTENCY: PASS
DESTRUCTIVE BEHAVIOR: NONE
EXTERNAL SIDE EFFECTS: NONE
FULL PROFILE DISABLED: YES
SCOPE CLEAN: YES
READY TO COMMIT: YES

## Delivery status

FEATURE HEAD: 81e46a22996cc1258203c1d8b47be3ea661be925
PUSHED: YES
PR: #9 (https://github.com/hoangquocquan/Django-web-t-123/pull/9)
PR CI: PENDING at last refresh; Django checks/tests and Phase 13.2 Test Pipeline have not completed. AWS validation, React build, Phase 6A runtime syntax, and PostgreSQL migration smoke are PASS.
READY TO MERGE: NO
MERGE PERFORMED: NO
