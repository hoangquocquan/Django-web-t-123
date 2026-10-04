# Phase 3B Master Data and RFQ Implementation Report

## 1. Project isolation evidence

- Working directory at isolation: `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO`.
- Git root: `C:/Users/hoang/Documents/ChatGPT/WEB Ô TÔ DJANGO`.
- Origin: `https://github.com/hoangquocquan/Django-web-t-123.git`.
- Canonical directories `django_backend/` and `figma_make_frontend/` both exist.
- Branch: `codex/demo-database-validation`.
- HEAD: `41753f485f437ecde2cf19e3101d856e7e96a54c`.
- Isolation result: PASS. No AI FACTORY path was read or modified.

## 2. Starting Git state

The initial status was:

```text
?? PHASE_3A_SCHEMA_AND_MIGRATION_PLAN_R2_REPORT.md
?? PHASE_3A_SCHEMA_AND_MIGRATION_PLAN_REPORT.md
?? docs/database/
```

These existing untracked Phase 3A artifacts were preserved. No commit, push,
branch switch, stash, reset, deletion, or unrelated overwrite was performed.

## 3. R2.1 idempotency clarification

`docs/database/PHASE_3A_SCHEMA_AND_MIGRATION_PLAN.md` was minimally clarified
to make idempotency mandatory only for retry-sensitive commercial commands:
RFQ creation, quotation creation/revision, and accepted-quotation conversion.
Normal Customer, Part, and Material CRUD relies on unique business codes.

The RFQ schema now contains nullable `idempotency_key` and `request_hash`, the
partial unique constraint `uq_rfq_idempotency_nonnull`, and the conditional
pair constraint `ck_rfq_idempotency_pair_v1`. Both values may be null until the
Phase 4 command layer exists. No API or command service was added.

## 4. Exact implementation files

- `docs/database/PHASE_3A_SCHEMA_AND_MIGRATION_PLAN.md`
- `django_backend/apps/foundation/migrations/0007_define_phase3b_permissions.py`
- `django_backend/apps/business_core/models.py`
- `django_backend/apps/business_core/business_numbers.py`
- `django_backend/apps/business_core/migrations/0003_businessmaterial_businessnumbersequence_and_more.py`
- `django_backend/apps/business_core/migrations/0004_mark_existing_master_rows_legacy.py`
- `django_backend/apps/business_core/migrations/0005_phase3b_master_constraints.py`
- `django_backend/apps/business_core/tests/test_phase3b_master_models.py`
- `django_backend/apps/sales/models.py`
- `django_backend/apps/sales/migrations/0002_salesrfq_salesrfqline_salesrfqdocument_and_more.py`
- `django_backend/apps/sales/tests/test_phase3b_rfq_models.py`
- `django_backend/tests/test_phase3b_migrations.py`
- `PHASE_3B_MASTER_DATA_RFQ_IMPLEMENTATION_REPORT.md`

## 5. Migration sequence and dependencies

1. `foundation.0007_define_phase3b_permissions` depends on
   `foundation.0006_add_login_audit_and_two_factor_challenges`.
2. `business_core.0003_businessmaterial_businessnumbersequence_and_more`
   depends on `business_core.0002_seed_business_core_from_legacy` and
   `foundation.0007_define_phase3b_permissions`. It creates the number/material
   tables and nullable additive master fields/indexes.
3. `business_core.0004_mark_existing_master_rows_legacy` depends on
   `business_core.0003...`. It keeps existing Customer/Product rows `LEGACY`
   and runs the active-database preflight before constraints.
4. `business_core.0005_phase3b_master_constraints` depends on
   `business_core.0004...` and activates named master constraints.
5. `sales.0002_salesrfq_salesrfqline_salesrfqdocument_and_more` depends on
   `sales.0001_sales_platform`, `business_core.0005...`, and
   `foundation.0007...`; it creates the complete RFQ schema and constraints.

All `RunPython` operations use historical models, the migration connection's
database alias, and idempotent operations. They do not use a legacy alias,
external file, network source, or environment-dependent data source.

## 6. Implemented schema

- `BusinessNumberSequence`: namespace, period, nonnegative counter, timestamps.
- `BusinessCustomer`: additive contract, customer code, archive timestamp, and
  stable creator/updater relationships; all legacy fields and PKs remain.
- `BusinessProduct`: additive Part code/revision/unit/material/spec/activity and
  actor fields; `sku`, legacy status/price/slug/SEO fields remain unchanged.
- `BusinessMaterial`: canonical material code, name, standard, grade,
  description, activity, legacy evidence ID, actors, and timestamps.
- `SalesRfq`: customer, lifecycle, dates, actors, optional quote family,
  closure reason, legacy evidence ID, and R2.1 idempotency storage.
- `SalesRfqLine`: positive Decimal quantity, positive per-RFQ line number,
  controlled unit, optional Part/Material, required dates and description.
- `SalesRfqDocument`: metadata only, UUID group/version, generated storage-key
  contract, MIME/size/SHA-256 metadata, replacement link, and uploader.
- `SalesTechnicalReview`: exact decision set, reason policy, requested fields,
  stable reviewer/RFQ evidence, and append-only model/queryset behavior.

No quotation, approval, order, progress, audit, endpoint, serializer, frontend,
file-storage integration, or AI functionality was implemented.

## 7. Business-number allocation

`business_numbers.py` supports exactly `CUS`, `PART`, `MAT`, `RFQ`, `QT`, and
`SO`. Master namespaces use `GLOBAL`; commercial namespaces use a four-digit
UTC year. Formats are the approved zero-padded forms. Allocation uses
`transaction.atomic()`, `select_for_update()`, a safe create-race recovery path,
and at most three integrity-collision attempts. Gaps are allowed. The code does
not claim SQLite locking parity.

## 8. Existing-data preflight and normalization

The default development SQLite file was zero bytes/unmigrated, so it was not
opened for schema writes and `migrate` was never run against it. Preflight was
implemented as an active-migration-database gate immediately before master
constraints. It counts:

- blank V1 company names;
- unknown V1 customer statuses;
- active V1 customers with neither email nor phone;
- duplicate proposed Customer, Part, and Material codes;
- invalid/missing V1 Part revision or unit;
- missing stable Customer, Part, or Material creator evidence.

Any nonzero applicable count raises
`BLOCKED_PHASE_3B_DATA_CONSTRAINT` before constraints are added.

On the managed existing-data migration fixture, one Customer and one Product
kept their original IDs, legacy IDs, names, slugs, and lowercase legacy status.
Both remained `data_contract=LEGACY`; all proposed-constraint violation counts
were zero because V1 checks do not reject grandfathered rows.

Deterministic normalization/backfill results:

- rows promoted to `MVP_V1`: 0;
- generated customer/part/material codes: 0;
- fabricated actor/contact/revision/unit/material values: 0;
- fixture rows verified as `LEGACY`: 1 Customer and 1 Product.

The two deliberately incomplete fixture rows are the exception evidence left
as `LEGACY`. The active default database supplied no migrated business rows to
classify. Future ambiguous production rows remain `LEGACY`; no guessing occurs.

## 9. Constraints and indexes activated

Master constraints include `uq_numseq_namespace_period`, sequence namespace,
period and nonnegative checks; partial Customer/Part code uniqueness and their
conditional V1 required/status/contact/unit checks; Material code/legacy-ID
uniqueness and V1-required checks.

RFQ constraints cover RFQ/quote-family/idempotency/legacy-ID uniqueness,
idempotency pair consistency, lifecycle, required fields, due-date ordering,
and closed reason. Line constraints cover unique positive line numbers,
positive quantity, unit, and description. Document constraints cover unique
group/version and storage key, positive version/size, 64-character hexadecimal
SHA-256, MIME allowlist, and required metadata. Review constraints cover its
exact decisions, conditional reason, and stable RFQ/reviewer evidence.

New indexes cover active Material names, active Part codes/default material,
Customer status/name, RFQ status/due/customer/assignee, RFQ document time and
checksum, and technical-review RFQ/time.

## 10. Permission definitions

The idempotent migration defines 18 ungranted actions:

- Customer: `view`, `create`, `change`, `archive`.
- Part: `view`, `manage`, `archive`.
- Material: `view`, `manage`, `archive`.
- RFQ/Technical Review: `view`, `create`, `change`, `archive`, `submit`,
  `review`, `document_upload`, `document_download`.

Tests verified that no `FoundationRolePermission` grants were created. Existing
permissions, roles, users, and role assignments remain unchanged.

## 11. Verification results

Commands were run from `django_backend/` against pytest's disposable in-memory
SQLite database; the default database was not migrated.

```text
python manage.py check
System check identified no issues (0 silenced).

python manage.py makemigrations --dry-run --check
No changes detected

pytest -q apps/business_core/tests/test_phase3b_master_models.py \
  apps/sales/tests/test_phase3b_rfq_models.py tests/test_phase3b_migrations.py
26 passed, 1 skipped in 11.46s

pytest -q
125 passed, 141 skipped in 12.06s

git diff --check
exit 0 (only Git's informational LF-to-CRLF warnings)
```

The migration tests cover clean migration, an existing managed-data fixture,
field/ID preservation, permission definitions without grants, and a static gate
against external legacy-database access. Focused model tests cover all requested
master/RFQ uniqueness, validation, metadata, append-only, and R2.1 cases.

## 12. PostgreSQL and SQLite evidence

PostgreSQL is not available in this workspace (`psql` was not found), and the
repository test setting explicitly uses `django.db.backends.sqlite3` with an
in-memory database. Therefore PostgreSQL constraint/concurrency acceptance is
not claimed. The separate-connection/barrier concurrency test is present and
is skipped unless `connection.vendor == "postgresql"`.

SQLite checks passed, including an explicit assertion that
`has_select_for_update` is false. SQLite verifies safe schema/model behavior
only; it is not evidence of PostgreSQL row-lock concurrency parity.

## 13. Compatibility, rollback, and recovery

All changes are additive. Existing Customer/Product primary keys, fields,
values, and consumers are preserved; no API/UI consumer was switched. New RFQ
tables are not exposed. Reversing the empty Phase 3B tables/schema is suitable
only on a disposable verification database. Contract classification is not
guessed on reverse. After any real `MVP_V1` write, deployed additive schema must
remain and recovery is a forward-fix.

## 14. Final diff audit

`git diff --stat` (tracked files only) before adding this untracked report:

```text
django_backend/apps/business_core/models.py | 268 +++++++++++++++++++++
django_backend/apps/sales/models.py         | 348 +++++++++++++++++++++++++++-
2 files changed, 615 insertions(+), 1 deletion(-)
```

All newly created migrations, tests, allocator, R2.1 plan, and this report are
untracked, so Git does not include them in ordinary `git diff --stat`. The final
status is recorded below. The pre-existing Phase 3A reports remain untouched.

```text
 M django_backend/apps/business_core/models.py
 M django_backend/apps/sales/models.py
?? PHASE_3A_SCHEMA_AND_MIGRATION_PLAN_R2_REPORT.md
?? PHASE_3A_SCHEMA_AND_MIGRATION_PLAN_REPORT.md
?? PHASE_3B_MASTER_DATA_RFQ_IMPLEMENTATION_REPORT.md
?? django_backend/apps/business_core/business_numbers.py
?? django_backend/apps/business_core/migrations/0003_businessmaterial_businessnumbersequence_and_more.py
?? django_backend/apps/business_core/migrations/0004_mark_existing_master_rows_legacy.py
?? django_backend/apps/business_core/migrations/0005_phase3b_master_constraints.py
?? django_backend/apps/business_core/tests/test_phase3b_master_models.py
?? django_backend/apps/foundation/migrations/0007_define_phase3b_permissions.py
?? django_backend/apps/sales/migrations/0002_salesrfq_salesrfqline_salesrfqdocument_and_more.py
?? django_backend/apps/sales/tests/test_phase3b_rfq_models.py
?? django_backend/tests/test_phase3b_migrations.py
?? docs/database/
```

No frontend file changed, so no frontend build was run. No AI FACTORY path,
external legacy database, production database/data, network source, or external
file store was read or modified.

## 15. Final verdict

`PHASE_3B_IMPLEMENTED_PENDING_POSTGRES_VALIDATION`
