# Phase 3C Quotation Implementation Report

## Final verdict

`READY_FOR_PHASE_3D`

Phase 3C canonical quotation schema, migrations, domain invariants, and focused
tests were completed and validated on PostgreSQL 16 on 2026-09-13 (Asia/Tokyo).
Phase 3D Orders/Production/Audit was not implemented.

## Project isolation

| Item | Result |
| --- | --- |
| Working directory | `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO` |
| Git root | `C:/Users/hoang/Documents/ChatGPT/WEB Ô TÔ DJANGO` |
| Repository | `https://github.com/hoangquocquan/Django-web-t-123.git` |
| Branch | `codex/demo-database-validation` |
| HEAD | `41753f485f437ecde2cf19e3101d856e7e96a54c` |
| `django_backend/` | present |
| `figma_make_frontend/` | present and unchanged |
| Isolation verdict | PASS |

The canonical business spec was found at
`docs/business/MINI_ENTERPRISE_BUSINESS_SPEC_V1.md`; the other authoritative
inputs were read from their requested repository paths.

The separate AI FACTORY workspace was not read or modified. Django n8n and Zalo
n8n were not started or changed. No legacy unmanaged table, API, frontend,
order, production, or audit implementation was changed. No commit, push, merge,
deployment, reset, clean, or stash occurred. Pre-existing tracked and untracked
worktree changes were preserved.

## Models implemented

### `SalesQuotation`

The existing managed table and primary key remain unchanged. Legacy fields
`opportunity`, `customer`, `quotation_number`, `version`, `status`,
`approval_status`, and existing actors/timestamps remain compatible.

Canonical additive fields implement one quotation revision per RFQ:

- `data_contract` (`LEGACY` or `MVP_V1`), nullable `rfq`, zero-based nullable
  `revision`, and canonical `workflow_status`;
- controlled `VND`/`USD` currency and required-for-V1 validity dates;
- Decimal(20,4) subtotal, discount, tax, and total fields;
- terms, immutable customer/RFQ JSON snapshots, send metadata, updater;
- retry-safe nullable idempotency key plus request hash.

For `MVP_V1` rows, commercial identity, RFQ/customer links, numbers, validity,
money, terms, snapshots, idempotency, and creator become immutable after the
draft is submitted. Invalid lifecycle jumps and deletion of submitted V1
revisions are rejected. Existing `LEGACY` consumers retain their compatibility
write path until the future Phase 4 cutoff.

### `SalesQuotationLine`

Existing product, description, quantity, price, discount, and total fields are
preserved; Decimal columns were widened without changing values. Canonical
fields add data contract, per-revision line number, protected source RFQ line,
part/material/unit snapshots, Decimal(20,4) line subtotal, and creation time.

V1 lines require a valid source line and canonical snapshots. Cross-RFQ source
links are rejected by domain validation. Header/line save, update, and delete
guards prevent in-place mutation once the quotation leaves `DRAFT`.

### Immutable decision evidence

- `SalesQuotationApprovalDecision`: one protected decision per revision,
  reviewer, `APPROVED`/`REJECTED`, reason, notes, and decision time.
- `SalesQuotationCustomerDecision`: one protected decision per revision,
  recorder, `ACCEPTED`/`DECLINED`, contact/evidence snapshots, reason, and time.

Both decision models reject update/delete through instance and queryset paths.
Rejection/decline reasons are database-enforced. Maker-checker is enforced by
model validation and the locked domain transaction because it crosses the
quotation-to-creator relationship.

## Domain invariants

`apps/sales/quotation_domain.py` contains backend-only domain operations; no API,
serializer, management command, or frontend surface was added.

- Parses finite Decimal values and rejects float authority.
- Uses `ROUND_HALF_UP`, USD quantum `0.01`, VND quantum `1`, and four-decimal
  storage.
- Calculates line subtotal/total and header subtotal/discount/tax/total; client
  totals are not accepted as input authority.
- Locks the RFQ, allocates a `QT-YYYY-NNNN` family once, computes `Max(revision)
  + 1`, and inserts the quotation plus snapshot lines atomically.
- Uses unique idempotency key/request-hash matching and a maximum of three
  integrity retries.
- Requires the latest revision to be rejected before rework; creation of the
  replacement atomically supersedes the rejected revision.
- Submits only balanced drafts, enforces maker-checker approval, records send
  evidence, and rejects acceptance after expiry.
- Locks the quotation family and prevents an accepted effective revision from
  being superseded.

## Migration sequence

1. `foundation.0008_define_phase3c_permissions` defines nine quotation actions
   idempotently and creates no role grants.
2. `sales.0003_phase3c_quotation_schema` adds nullable/default-safe columns,
   widens Decimal fields, creates empty decision tables, and adds indexes. It
   does not activate V1 constraints.
3. `sales.0004_classify_phase3c_legacy_quotations` marks only ambiguous existing
   quotation/header rows `LEGACY`, performs V1/collision/money/decision
   preflight, and stops with `BLOCKED_PHASE_3C_DATA_CONSTRAINT` on violations.
4. `sales.0005_phase3c_quotation_constraints` activates the named unique/check
   constraints after classification and preflight.

All migration data access uses the active migration alias and historical
models. No migration reads an external legacy file, URL, database alias, or
unmanaged quotation table.

## Legacy compatibility decisions

- Existing quotation/header primary keys and all prior field values remain
  exact and readable.
- Existing rows receive `data_contract=LEGACY`; canonical RFQ, revision,
  workflow, currency, idempotency, source-line, and snapshot fields remain
  null/blank.
- `status` is not mapped to `workflow_status`; one-based `version` is not mapped
  to zero-based `revision` without evidence.
- No RFQ link, quotation family, revision, approval, customer decision, actor,
  currency, validity, snapshot, or money correction is fabricated.
- Migration tests verified forward migration and safe reverse to Phase 3B while
  retaining exact legacy fields/rows.

## Constraints and indexes

PostgreSQL introspection confirmed all 28 named Phase 3C constraints/partial
unique indexes.

Header constraints:

- `uq_quote_rfq_revision`, `uq_quote_effective_rfq`,
  `uq_quote_idempotency_nonnull`;
- `ck_quote_workflow_status`, `ck_quote_v1_required`, `ck_quote_currency`,
  `ck_quote_validity`, `ck_quote_money_nonneg`, `ck_quote_discount_bound`,
  `ck_quote_total_equation`, `ck_quote_idempotency_pair`,
  `ck_quote_request_hash`.

Line constraints:

- `uq_quoteline_parent_number`;
- `ck_quoteline_number_pos`, `ck_quoteline_quantity_pos`,
  `ck_quoteline_price_pos`, `ck_quoteline_money_nonneg`,
  `ck_quoteline_unit`, `ck_quoteline_v1_required`,
  `ck_quoteline_discount_bound`, `ck_quoteline_total_equation`.

Decision constraints:

- `uq_quote_approval_decision`, `ck_quoteapproval_decision`,
  `ck_quoteapproval_reason`;
- `uq_quote_customer_decision`, `ck_quotecustomer_decision`,
  `ck_quotecustomer_required`, `ck_quotecustomer_reason`.

New indexes confirmed: `sales_quote_rfq_rev_idx`,
`sales_quote_flow_valid_idx`, and `sales_quote_creator_idx`. Existing quotation
number/status/approval indexes remain intact.

## PostgreSQL validation and isolation

| Item | Evidence |
| --- | --- |
| Docker Client | 29.4.3, API 1.54, windows/amd64 |
| Docker Server Engine | 29.4.3, API 1.54, linux/amd64 |
| Docker Desktop | 4.74.0 (227015) |
| PostgreSQL | 16.14 (Debian 16.14-1.pgdg13+1), 64-bit |
| Image | `postgres:16` |
| Container | `django-phase3c-postgres16-validation-20260913` |
| Database | `django_phase3c_validation_20260913` |
| Bind | `127.0.0.1:55434 -> 5432/tcp` |
| Network | `django-phase3c-validation-net-20260913` (task-owned) |
| Storage | task-owned tmpfs; no bind or Docker volume |
| Health | healthy within bounded wait |

The password was generated in process, was never printed or stored in a file,
and was used only through process-local `DATABASE_URL`. Tests explicitly used
`config.settings.base` so PostgreSQL was not replaced by the SQLite test
settings.

Only the named task-owned container and network were stopped and removed.
Post-cleanup verification returned:

```text
CONTAINER_REMOVED=YES
NETWORK_REMOVED=YES
PORT_55434=FREE
PHASE3C_TEMP_DIRS=NONE
```

No Docker inventory was listed and no pre-existing container, network, volume,
or database was reused or modified.

## Test results

| Suite/gate | Result |
| --- | --- |
| Django system check | PASS: 0 issues |
| Migration consistency | PASS: no changes detected |
| Clean PostgreSQL migrations | PASS: all migrations through sales 0005 |
| Final PostgreSQL `migrate --check` | PASS |
| Focused Phase 3C SQLite | 17 passed, 1 PostgreSQL-only skip |
| Full backend SQLite compatibility | 141 passed, 142 skipped |
| Focused Phase 3C PostgreSQL | 18 passed, 0 skipped/failed |
| Focused Phase 3B PostgreSQL preservation | 26 passed, 1 SQLite-only skip |
| Full backend PostgreSQL regression | 143 passed, 141 skipped, 0 failed/errors |
| Python compile and `git diff --check` | PASS |

The first focused SQLite iteration exposed three new-test issues: UTC `.date()`
was being compared with Asia/Tokyo local dates in two paths, and one validation
message did not match its assertion. These were corrected with
`timezone.localdate()` and the final SQLite/PostgreSQL results above are the
authoritative runs.

## Concurrency, rollback, and duplicate evidence

- PostgreSQL 20-way next-revision race: one caller atomically created R1; the
  other 19 received controlled conflicts after observing the new draft.
- Persisted revisions were exactly `[0, 1]`; duplicate revisions: 0.
- R0/R1 reused one RFQ quotation family; no second family number was allocated.
- The forced failure after family allocation rolled back the RFQ family field,
  QT sequence row, quotation header, and lines: all four residual counts were 0.
- Maker-checker failure created 0 decisions and left the quotation
  `PENDING_APPROVAL`.
- Expired acceptance created 0 customer decisions and left the quotation
  `SENT`.
- Expected uniqueness/constraint failures left no partially committed records.
- Final duplicate audit returned zero groups for RFQ/revision, quotation number,
  idempotency key, line number, approval decision, and customer decision.
- Nine Phase 3C permission definitions exist with zero role grants.

## Changed files and SHA256

`sales/models.py` already contained the uncommitted Phase 3B work and was
extended in place for Phase 3C. The other listed files are Phase 3C additions.
The report omits its own hash because embedding it would be self-referential.

```text
9c2d0c18c6e19b07877769638ec8cba1aa70627909518167086c94aaf5068a0b  django_backend/apps/sales/models.py
3f0a916002c5e7cbbc85cf8ec23ca775e19559014c41af2ec5b504c92498d69a  django_backend/apps/sales/quotation_domain.py
16917e3a3da4e9b4576cc6ddbbaf208894f5e57485c5d9762755757478db7470  django_backend/apps/foundation/migrations/0008_define_phase3c_permissions.py
63eee595a91dace48f859eaeb6e741aaaaf383e0536197cc6f8a87d102c98318  django_backend/apps/sales/migrations/0003_phase3c_quotation_schema.py
b4567f9c14a2a9048f8cbd44a0040e61668cd5d3fda7d78224bab1308b473c87  django_backend/apps/sales/migrations/0004_classify_phase3c_legacy_quotations.py
7fe412c6ef092cbd5979c3ae27867f6c237df0d37496d4afde7cdc4406afe0f6  django_backend/apps/sales/migrations/0005_phase3c_quotation_constraints.py
41d63174b726d58feec8834bdd35d617464f6617b65c7a5f7d582246474e0f9d  django_backend/apps/sales/tests/test_phase3c_quotation_models.py
99ddb3ff6c93e31c3589bfc8baa9f8da79869a9852313ca816e489c73c18bf96  django_backend/tests/test_phase3c_migrations.py
```

## Remaining blockers

None for Phase 3C. Phase 3D may begin only as a separate explicitly authorized
task. Production/data deployment remains outside this implementation task.
