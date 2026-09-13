# Phase 4B — Master Data and RFQ Command API Implementation Report

## Scope and isolation

Implemented the Phase 4B canonical command boundary only.  The working directory
was `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO`; Git root was the same;
branch was `codex/demo-database-validation` at
`d6fded591ecf0c013d91e74eefcd94d48ad6f312`; origin was
`https://github.com/hoangquocquan/Django-web-t-123.git`.  Both
`django_backend/` and `figma_make_frontend/` were present.  No AI FACTORY,
n8n, Zalo n8n, 9Router, or unrelated Docker resource was inspected or changed.

There are no Phase 4B migrations.  The command boundary deliberately uses the
canonical Phase 3B models and constraints (`BusinessCustomer`, `BusinessProduct`,
`BusinessMaterial`, `SalesRfq`, `SalesRfqLine`, `SalesRfqDocument`,
`SalesTechnicalReview`, `AuditEvent`) without changing their schema or any
legacy unmanaged table.

## Implemented command boundary

Added strict, unknown-field-rejecting input serializers, an explicit command
permission matrix, atomic domain services, command views, and canonical routes.
All write endpoints are explicit commands under `/api/v1/canonical/`; Phase 4A
read routes and legacy routes remain unchanged.

| Resource | Commands |
| --- | --- |
| Customer | create, update, archive (deactivate) |
| Part | create, update, archive |
| Material | create, update, archive |
| RFQ | create, update, submit, archive, resubmit |
| RFQ line | add, update, remove |
| Technical review | start, request-information, complete, decline, acknowledge-declined |
| RFQ document | upload, version upload, authenticated download/HEAD |

Master-data numbering uses the existing locked Phase 3B allocator.  RFQ create
uses an actor-bound request hash and `Idempotency-Key`; equal retries return the
same RFQ while a conflicting payload is rejected atomically.  RFQ revisions,
state transitions, ownership, legacy-row denial, technical-review reason rules,
submission readiness, append-only review evidence, and audit writes are all
validated in transactional services.  Audit events are emitted only through the
existing approved action catalogue; customer and RFQ lifecycle actions are
covered by focused tests.

The command RBAC boundary is fail-closed: it requires an active user, an allowed
role, and both the exact command permission and exact module `view` permission.
`*:*`, unassigned roles, inactive users, and legacy records do not grant command
access.  Customer and RFQ mutations are Admin/Sales as applicable; Part and
Material mutations are Admin-only; technical review is Manager-only; document
download is available only to the defined authorized roles.

## Documents and data protection

RFQ upload/version commands enforce the Phase 3B PDF, STEP/STP, DXF and XLSX
extension/MIME allowlists, bounded size, format signatures, ZIP traversal and
ZIP-bomb checks, normalized safe filenames, generated opaque storage keys, and
safe-storage/symlink-escape validation.  Stored files are created before their
metadata record only within a transaction and are deleted only when that newly
created write fails; pre-existing versions are not deleted.  Downloads authorize
before opening storage, set a safe attachment filename and do not expose storage
keys, absolute paths, storage errors, exception text, token-like values, or
arbitrary metadata.

## Compatibility and test-isolation correction

No RFQ links, numbering, revisions, approvals, decisions, or business data were
fabricated.  Existing legacy records remain readable through Phase 4A but are
not mutable via canonical commands.

One test-only Phase 3D correction was necessary for a clean PostgreSQL database:
`test_rbac_legacy_unassigned_and_sales_progress_fail_closed` now creates its own
fixture-only wildcard permission with `get_or_create`.  The test verifies that
the wildcard is denied, so this removes an accidental dependency on test order
without changing application RBAC, models, migrations, or production seed data.

## Validation evidence

Static and SQLite validation:

- `python manage.py check` — passed.
- `python manage.py makemigrations --check --dry-run` — `No changes detected`.
- `python -m compileall` for changed Python paths — passed.
- `git diff --check` — passed (only Git's line-ending advisory was emitted).
- Focused Phase 4B SQLite — `17 passed, 1 skipped`.
- Phase 4A SQLite preservation — `16 passed`.
- Full backend SQLite — `189 passed, 144 skipped`.

PostgreSQL validation used Docker Client 29.4.3, Docker Server 29.4.3 / Docker
Desktop 4.74.0, and PostgreSQL `16.14 (Debian 16.14-1.pgdg13+1)`.  The single
task-owned container was
`django-phase4b-postgres16-validation-20260913-d6fded01`, labelled
`com.openai.task=django-phase4b-20260913-d6fded01` and
`com.openai.repo=Django-web-t-123`, with only
`127.0.0.1:55437 -> 5432`.  Its distinct task-owned network and volume carried
the same labels.

- Applied all migrations and `migrate --check` — passed.
- Focused Phase 4B PostgreSQL including 20 simultaneous RFQ creates — `18 passed`.
- Phase 4A PostgreSQL preservation — `16 passed`.
- Phase 3B/3C/3D preservation was run on PostgreSQL; a clean-database fixture
  dependency was found and corrected as above.
- Full PostgreSQL backend regression after the correction — `192 passed, 141 skipped`.

The concurrent RFQ test verified unique family numbers, sequence allocation, and
transactional rollback.  Focused tests also verify duplicate/idempotency
conflicts, invalid transitions, rejected uploads, storage rollback, forced audit
rollback, document version preservation, and non-mutating Phase 4A reads.

## Changed files and SHA-256

| Path | SHA-256 |
| --- | --- |
| `django_backend/apps/api/canonical_contract.py` | `094DC32D329617EC6E8217D225CAB16DD19F579489139F36081E6C1D2AB05DDA` |
| `django_backend/apps/api/canonical_permissions.py` | `169A75E3F3F257FA53CEF7562F59746CFB6FA0ECE06A001BA33CDD9EF085D022` |
| `django_backend/apps/api/canonical_urls.py` | `259EF875951D8F43DBAC729E8E70957D42D87607DF37808A2F17CBE84DBF2450` |
| `django_backend/apps/api/serializers/canonical_commands.py` | `98A811AA21058ABCC031E32011574BD6016CD630AB6A0756755D6087DA766A9F` |
| `django_backend/apps/api/services/canonical_command_service.py` | `9C9C37D545F20530263AF22E86DF48844EE01A0A6DFB0A940570996CE9FB899A` |
| `django_backend/apps/api/views/canonical_commands.py` | `14AED3B0217B45E4C1F3BBC048FA2D58A38EF74E62E856C691CDD8BB1558670F` |
| `django_backend/apps/api/tests/test_phase4b_master_data_rfq_commands.py` | `20363BF8842C2C22DCD5069CB69B73E0A6FB95EE46E5B36204C3DC2D87991D89` |
| `django_backend/apps/transaction_domain/tests/test_phase3d_order_domain.py` | `99D8E4533FE778A0A9715D0507F16951E048E54E7C771A7414B6D16C154EF3CA` |

This report is the ninth changed path; its final SHA-256 is recorded in the
terminal closure after cleanup.  No commit, push, merge, deployment, branch
change, or Phase 4C implementation was performed.

## PostgreSQL and evidence closure addendum

Phase 4B evidence closure was resumed from the same isolated project state:

- Current working directory: `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO`.
- Git root: `C:/Users/hoang/Documents/ChatGPT/WEB Ô TÔ DJANGO`.
- Branch: `codex/demo-database-validation`.
- HEAD: `d6fded591ecf0c013d91e74eefcd94d48ad6f312`.
- Origin: `https://github.com/hoangquocquan/Django-web-t-123.git`.
- `django_backend/` and `figma_make_frontend/` were present.

Initial and final Git status were the same Phase 4B-only path set:

```text
 M django_backend/apps/api/canonical_contract.py
 M django_backend/apps/api/canonical_permissions.py
 M django_backend/apps/api/canonical_urls.py
 M django_backend/apps/transaction_domain/tests/test_phase3d_order_domain.py
?? PHASE_4B_MASTER_DATA_RFQ_COMMAND_API_IMPLEMENTATION_REPORT.md
?? django_backend/apps/api/serializers/canonical_commands.py
?? django_backend/apps/api/services/canonical_command_service.py
?? django_backend/apps/api/tests/test_phase4b_master_data_rfq_commands.py
?? django_backend/apps/api/views/canonical_commands.py
```

Complete working-tree path classification:

| Path | Classification |
| --- | --- |
| `django_backend/apps/api/canonical_contract.py` | Phase 4B implementation |
| `django_backend/apps/api/canonical_permissions.py` | Phase 4B implementation |
| `django_backend/apps/api/canonical_urls.py` | Phase 4B implementation |
| `django_backend/apps/api/serializers/canonical_commands.py` | Phase 4B implementation |
| `django_backend/apps/api/services/canonical_command_service.py` | Phase 4B implementation |
| `django_backend/apps/api/views/canonical_commands.py` | Phase 4B implementation |
| `django_backend/apps/api/tests/test_phase4b_master_data_rfq_commands.py` | Phase 4B focused tests |
| `django_backend/apps/transaction_domain/tests/test_phase3d_order_domain.py` | Phase 3D test-isolation correction |
| `PHASE_4B_MASTER_DATA_RFQ_COMMAND_API_IMPLEMENTATION_REPORT.md` | Authoritative Phase 4B report |

Static and SQLite closure commands:

| Command | Passed | Failed | Errors | Skipped | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `python manage.py check` | n/a | 0 | 0 | n/a | `System check identified no issues (0 silenced).` |
| `python manage.py makemigrations --check --dry-run` | n/a | 0 | 0 | n/a | `No changes detected` |
| `python -m compileall -q apps\api\canonical_contract.py apps\api\canonical_permissions.py apps\api\canonical_urls.py apps\api\serializers\canonical_commands.py apps\api\services\canonical_command_service.py apps\api\views\canonical_commands.py apps\api\tests\test_phase4b_master_data_rfq_commands.py apps\transaction_domain\tests\test_phase3d_order_domain.py` | n/a | 0 | 0 | n/a | Passed |
| `git diff --check` | n/a | 0 | 0 | n/a | Passed; only Git LF/CRLF advisory lines were emitted |
| `python -m pytest -q apps\api\tests\test_phase4b_master_data_rfq_commands.py` | 17 | 0 | 0 | 1 | Passed in 6.83s |
| `python -m pytest -q apps\api\tests\test_phase4a_canonical_read_api.py` | 16 | 0 | 0 | 0 | Passed in 6.15s |
| `python -m pytest -q` | 189 | 0 | 0 | 144 | Passed in 70.15s |

PostgreSQL 16 closure used Docker Client `29.4.3`, Docker Server Engine
`29.4.3`, Docker Desktop `4.74.0`, and PostgreSQL server
`16.14 (Debian 16.14-1.pgdg13+1)`.

The closure database was migrated from an empty task-owned PostgreSQL database
with:

```text
$env:DATABASE_URL='postgresql://phase4b_user:phase4b_password@127.0.0.1:55437/phase4b_closure'
python manage.py migrate --noinput
```

All migrations applied successfully.

PostgreSQL commands and isolated suite totals:

| Suite | Command | Passed | Failed | Errors | Skipped | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Phase 4B command API | `python -m pytest -q --ds=config.settings.development apps\api\tests\test_phase4b_master_data_rfq_commands.py` | 18 | 0 | 0 | 0 | Passed in 20.42s |
| Phase 4A preservation | `python -m pytest -q --ds=config.settings.development apps\api\tests\test_phase4a_canonical_read_api.py` | 16 | 0 | 0 | 0 | Passed in 16.77s |
| Phase 3B preservation | `python -m pytest -q --ds=config.settings.development apps\business_core\tests\test_phase3b_master_models.py apps\sales\tests\test_phase3b_rfq_models.py` | 22 | 0 | 0 | 1 | Passed in 15.08s |
| Phase 3C preservation | `python -m pytest -q --ds=config.settings.development apps\sales\tests\test_phase3c_quotation_models.py` | 15 | 0 | 0 | 0 | Passed in 14.51s |
| Phase 3D corrected test alone | `python -m pytest -q --ds=config.settings.development apps\transaction_domain\tests\test_phase3d_order_domain.py::test_rbac_legacy_unassigned_and_sales_progress_fail_closed` | 1 | 0 | 0 | 0 | Passed in 13.16s |
| Phase 3D preservation | `python -m pytest -q --ds=config.settings.development apps\transaction_domain\tests\test_phase3d_order_domain.py` | 12 | 0 | 0 | 0 | Passed in 18.48s |
| Full backend PostgreSQL | `python -m pytest -q --ds=config.settings.development` | 192 | 0 | 0 | 141 | Passed in 105.35s |

Each PostgreSQL suite was run in a separate pytest process, so Django created
and destroyed its own isolated test database lifecycle for that command.  The
Phase 3D corrected test also passed alone before the complete Phase 3D suite,
proving that its result no longer depends on suite ordering.

The Phase 3D correction is limited to test fixture setup:

```diff
-    wildcard = FoundationPermission.objects.get(module="*", action="*")
+    wildcard, _ = FoundationPermission.objects.get_or_create(
+        module="*",
+        action="*",
+        defaults={
+            "name": "Legacy wildcard permission",
+            "description": "Fixture-only wildcard permission used to verify fail-closed RBAC.",
+        },
+    )
```

This does not weaken RBAC because the wildcard permission is still granted to
the legacy role used by the test, and the denial assertion remains unchanged:
the test still expects `change_order_progress(... legacy_user ...)` to raise
`PermissionDenied`.  No application code, migrations, seed data, or canonical
RBAC rules were changed by this correction.

Docker isolation evidence:

- Port check before creation: `PORT_55437_FREE=True`.
- Container name: `django-phase4b-closure-postgres16-20260913-d6fded59`.
- Container ID: `5e7cb3a1a2f46fe81c84b44d681a94833593329911d0a2c645424f7c25fd247f`.
- Container image: `postgres:16`.
- Container image ID: `sha256:33f923b05f64ca54ac4401c01126a6b92afe839a0aa0a52bc5aeb5cc958e5f20`.
- Container created: `2026-09-13T03:25:43.093365741Z`.
- Network name: `django-phase4b-closure-net-20260913-d6fded59`.
- Network ID: `80fd8802d048211765197e276a99d9df88eb5ab254f0dcc2f42b4344dc67a286`.
- Volume name: `django-phase4b-closure-pg16-data-20260913-d6fded59`.
- Volume created: `2026-09-13T03:25:31Z`.
- Ownership labels on container, network, and volume:
  `com.openai.task=django-phase4b-closure-20260913-d6fded59`,
  `com.openai.repo=Django-web-t-123`,
  `com.openai.phase=phase4b-postgresql-evidence-closure`.
- Port mapping: `127.0.0.1:55437 -> 5432/tcp`.
- Mounted volume: `django-phase4b-closure-pg16-data-20260913-d6fded59:/var/lib/postgresql/data`;
  Docker source
  `/var/lib/docker/volumes/django-phase4b-closure-pg16-data-20260913-d6fded59/_data`.

Cleanup evidence:

- `docker rm -f django-phase4b-closure-postgres16-20260913-d6fded59` returned
  `django-phase4b-closure-postgres16-20260913-d6fded59`.
- `docker network rm django-phase4b-closure-net-20260913-d6fded59` returned
  `django-phase4b-closure-net-20260913-d6fded59`.
- `docker volume rm django-phase4b-closure-pg16-data-20260913-d6fded59`
  returned `django-phase4b-closure-pg16-data-20260913-d6fded59`.
- Exact-name container inspect after cleanup returned
  `error: no such object: django-phase4b-closure-postgres16-20260913-d6fded59`.
- Exact-name network inspect after cleanup returned
  `network django-phase4b-closure-net-20260913-d6fded59 not found`.
- Exact-name volume inspect after cleanup returned
  `no such volume`.
- Port check after cleanup: `PORT_55437_FREE=True`.

Final SHA-256 for changed implementation and test files:

| Path | SHA-256 |
| --- | --- |
| `django_backend/apps/api/canonical_contract.py` | `094DC32D329617EC6E8217D225CAB16DD19F579489139F36081E6C1D2AB05DDA` |
| `django_backend/apps/api/canonical_permissions.py` | `169A75E3F3F257FA53CEF7562F59746CFB6FA0ECE06A001BA33CDD9EF085D022` |
| `django_backend/apps/api/canonical_urls.py` | `259EF875951D8F43DBAC729E8E70957D42D87607DF37808A2F17CBE84DBF2450` |
| `django_backend/apps/api/serializers/canonical_commands.py` | `98A811AA21058ABCC031E32011574BD6016CD630AB6A0756755D6087DA766A9F` |
| `django_backend/apps/api/services/canonical_command_service.py` | `9C9C37D545F20530263AF22E86DF48844EE01A0A6DFB0A940570996CE9FB899A` |
| `django_backend/apps/api/views/canonical_commands.py` | `14AED3B0217B45E4C1F3BBC048FA2D58A38EF74E62E856C691CDD8BB1558670F` |
| `django_backend/apps/api/tests/test_phase4b_master_data_rfq_commands.py` | `20363BF8842C2C22DCD5069CB69B73E0A6FB95EE46E5B36204C3DC2D87991D89` |
| `django_backend/apps/transaction_domain/tests/test_phase3d_order_domain.py` | `99D8E4533FE778A0A9715D0507F16951E048E54E7C771A7414B6D16C154EF3CA` |

## Remaining blockers and verdict

No implementation or validation blocker remains.  Closure removed the verified
task-owned container, network, and volume; exact-name inspections then returned
not found and host port 55437 was free.

**READY_FOR_PHASE_4C**
