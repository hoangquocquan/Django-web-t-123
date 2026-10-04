# Phase 3B PostgreSQL Validation Final Report

## Final verdict

`READY_FOR_PHASE_3C`

Validation completed on 2026-09-12 (Asia/Tokyo). Phase 3C was not implemented.

## Project isolation

| Item | Result |
| --- | --- |
| Working directory | `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO` |
| Git repository root | `C:/Users/hoang/Documents/ChatGPT/WEB Ô TÔ DJANGO` |
| Repository | `https://github.com/hoangquocquan/Django-web-t-123.git` |
| Branch | `codex/demo-database-validation` |
| HEAD | `41753f485f437ecde2cf19e3101d856e7e96a54c` |
| `django_backend/` | present |
| `figma_make_frontend/` | present |
| Isolation result | PASS |

The separate AI FACTORY workspace was not read or modified. Existing Docker
containers, networks, volumes, and databases were not listed, reused, or
modified. Django n8n and Zalo n8n were not started or changed. Existing
worktree changes were preserved; no reset, clean, stash, commit, push, merge,
deployment, or Phase 3C implementation occurred.

## Runtime identity and isolation

The supported out-of-sandbox approval path succeeded for Docker access.

| Item | Result |
| --- | --- |
| Docker Client | 29.4.3, API 1.54, windows/amd64 |
| Docker Server Engine | 29.4.3, API 1.54, linux/amd64 |
| Docker Desktop | 4.74.0 (227015) |
| PostgreSQL Server | 16.14 (Debian 16.14-1.pgdg13+1), 64-bit |
| Image | `postgres:16` |
| Container | `django-phase3b-postgres16-validation-20260912-resume` |
| Database | `django_phase3b_validation_20260912` |
| Bind | `127.0.0.1:55433 -> 5432/tcp` |
| Network | `django-phase3b-validation-net-20260912-resume` (task-owned) |
| Data storage | task-owned tmpfs at `/var/lib/postgresql/data`; no bind or Docker volume |
| Health gate | healthy within bounded wait |

The database password was randomly generated in process, was not printed or
written to a file, and was used only through a process-local `DATABASE_URL`.
Tests explicitly used `DJANGO_SETTINGS_MODULE=config.settings.base` (and pytest
`--ds=config.settings.base`) so the repository's SQLite-only test settings did
not replace PostgreSQL evidence.

## Validation commands and results

| Stage | Result |
| --- | --- |
| `docker version` through `require_escalated` | PASS: Client and Server confirmed |
| PostgreSQL `pg_isready` health gate | PASS |
| `python manage.py check` | PASS: 0 issues |
| `python manage.py makemigrations --check --dry-run` | PASS: no changes detected |
| Clean `python manage.py migrate --noinput` | PASS: all migrations applied |
| Final `python manage.py migrate --check` | PASS: no unapplied migrations |
| Focused Phase 3B pytest suite | PASS: 26 passed, 1 skipped, 0 failed |
| Full backend PostgreSQL regression rerun | PASS: 125 passed, 141 skipped, 0 failed/errors |
| Custom concurrency/rollback/constraint audit | PASS |
| Final duplicate audit | PASS |

Focused tests:

```text
apps/business_core/tests/test_phase3b_master_models.py
apps/sales/tests/test_phase3b_rfq_models.py
tests/test_phase3b_migrations.py

26 passed, 1 skipped in 23.46s
```

The one focused skip was the SQLite-only fallback limitation assertion; the
PostgreSQL allocator concurrency test executed and passed.

The first full-suite attempt reached `90 passed, 141 skipped, 35 errors`. Every
error had the same setup cause: Windows denied pytest access to
`C:\Users\hoang\AppData\Local\Temp\pytest-of-hoang`. There were no failed test
assertions and no PostgreSQL errors. The suite was rerun with a verified-new,
task-owned `--basetemp` inside `django_backend`; it completed successfully:

```text
125 passed, 141 skipped in 23.70s
```

The basetemp directory was removed after the run. Skipped tests were the
repository's environment/legacy-artifact conditional tests; the required Phase
3B PostgreSQL tests were included in the passing set.

## Numbering and concurrency evidence

Twenty concurrent allocations were run for every required business-number
namespace, after creating a dedicated sequence row for each namespace/period:

| Namespace | Allocations | Unique | Duplicates | Final counter |
| --- | ---: | ---: | ---: | ---: |
| CUS | 20 | 20 | 0 | 20 |
| PART | 20 | 20 | 0 | 20 |
| MAT | 20 | 20 | 0 | 20 |
| RFQ | 20 | 20 | 0 | 20 |

The CUS counter rollback probe began at 20, allocated inside a transaction that
raised an expected failure, and remained at 20 afterward. The next committed
allocation returned `CUS-0021`, proving the failed allocation did not consume
or partially commit a number.

## Idempotency, constraints, and failure atomicity

The focused PostgreSQL tests passed the RFQ idempotency-pair checks, uniqueness
of non-null idempotency keys, Customer/Part/Material/RFQ number uniqueness,
required-field checks, RFQ due-date and closure rules, RFQ line constraints,
document metadata/version/storage constraints, and append-only technical review
rules.

Additional database probes attempted expected constraint failures for Customer,
Part, Material, and RFQ (including duplicate RFQ idempotency). For each model,
the row count before and after the failed transaction was identical, with zero
partially committed records.

The final duplicate audit found zero duplicate groups for:

- `customer_code`
- `part_code`
- `material_code`
- `rfq_number`
- non-null RFQ `idempotency_key`

## Cleanup evidence

Only task-owned resources were stopped and removed:

```text
Container removed: YES
Task-owned network removed: YES
Host port 55433 after cleanup: FREE
Task-owned pytest basetemp removed: YES
```

No existing Docker resource was stopped, removed, or modified.

## Preserved Git state and SHA256

Final validation preserved the pre-existing tracked and untracked changes. The
report omits its own SHA256 because embedding a file's digest inside itself is
self-referential.

```text
4707efb5905714a5e4a74e8ead196ec9cc497dd46c749d71ea780c55df6516f5  django_backend/apps/business_core/models.py
7420724ff1ed16b5435014835cacebd8320cb78cf149b32dea79017a19868990  django_backend/apps/sales/models.py
ed8f30f7d718928809e387bdd1c208ebc12489b8811fb3cbb3a4c321a25c47e4  DOCKER_DESKTOP_WSL_DIAGNOSTIC_REPORT.md
ec2e1b3affa231d5ebfbbe9cff26de5402fa6c4a96e6f559e7f2d2c0f335e9e9  PHASE_3A_SCHEMA_AND_MIGRATION_PLAN_R2_REPORT.md
8a072db165c6f8a56281cf6b166e2e5f3d528cbc66c36f31f51efe76b3d86290  PHASE_3A_SCHEMA_AND_MIGRATION_PLAN_REPORT.md
f9579e7d25c61e1fa1e0f26f21d7af8f6abc0be28c9396a56143492f3b1c41a3  PHASE_3B_DOCKER_SANDBOX_PERMISSION_BLOCK_REPORT.md
34cd83f4912c48a8333eab712b725bb015f07d69e7778daa25ca5e64f0e49bd2  PHASE_3B_MASTER_DATA_RFQ_IMPLEMENTATION_REPORT.md
aab1f8021783929ac0e9665a81d96820b280f70eaabed834c10f2177c29fdf0d  PHASE_3B_POSTGRESQL_VALIDATION_CLOSURE_REPORT.md
a13d684aa24d0f24bc9c378e0c808e22cda632a1f9b4a64b0a9e90a11ae4c38b  PHASE_3B_POSTGRESQL_VALIDATION_HANDOFF_TO_CHATGPT.md
0e3cdbcaff8c1612f829ac6a34752beb536bdbaae943aed03503be92d5c2fda9  django_backend/apps/business_core/business_numbers.py
e98fea7dd5e96efcc55037d957a0fe3a06d36edd7e5c6ab1283dbca2bef9ea53  django_backend/apps/business_core/migrations/0003_businessmaterial_businessnumbersequence_and_more.py
850c8d315cf05d292d04728d1b6e842713fc146a81b60269c40cf743a04ee7a7  django_backend/apps/business_core/migrations/0004_mark_existing_master_rows_legacy.py
b2556086b6ef8ba463dfc0300851b4125e3044975d8267a68a08ac4a08905fec  django_backend/apps/business_core/migrations/0005_phase3b_master_constraints.py
32ce0dc3373a3dfc497207248b0e1ea260a00e17e905ee5622887d4f2d358a4  django_backend/apps/business_core/tests/test_phase3b_master_models.py
c59dbace55fee06feb91770cf71d03d0db0f6471736088681bd7b09df9b429fd  django_backend/apps/foundation/migrations/0007_define_phase3b_permissions.py
507e9fcab5122f9072e9b34bd93c6b251efe891637cf6657c68957a967719e68  django_backend/apps/sales/migrations/0002_salesrfq_salesrfqline_salesrfqdocument_and_more.py
3ff97b75ec05878129f577ee82463d3289084e4d6611119d8cd6bb8be6d20b56  django_backend/apps/sales/tests/test_phase3b_rfq_models.py
2ac7e011f1f1a69331794a784c99653c8028c7e8a804a12b4121b5f22acacd4f  django_backend/tests/test_phase3b_migrations.py
1122cbddd92829ead53bb299c076583280122fdf12ecaae7fd80445c63679590  docs/database/PHASE_3A_SCHEMA_AND_MIGRATION_PLAN.md
```

## Remaining blockers

None for Phase 3B PostgreSQL validation. Phase 3C may begin only as a separate,
explicitly authorized task.
