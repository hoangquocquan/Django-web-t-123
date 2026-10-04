# Phase 3A Schema and Migration Plan R2 Report

## Verdict

`PASS`

Conclusion: `READY_FOR_PHASE_3B`.

R2 makes the Phase 3A plan implementation-ready at field, constraint, mapping,
numbering, money, migration-boundary, test, and risk-control level. This task
changed documentation only; it did not implement Phase 3B.

## Project Isolation Check

| Check | Result |
| --- | --- |
| CWD | `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO` |
| Git root | `C:/Users/hoang/Documents/ChatGPT/WEB Ô TÔ DJANGO` |
| Repository | `https://github.com/hoangquocquan/Django-web-t-123.git` |
| Branch | `codex/demo-database-validation` |
| `django_backend/` | present |
| `figma_make_frontend/` | present |
| AI FACTORY | not read, modified, or accessed |

Isolation verdict: `PASS`.

## Baseline and working tree

- Base checkpoint: `41753f485f437ecde2cf19e3101d856e7e96a54c`.
- Checkpoint subject: `chore: stabilize project and define MVP business contract`.
- HEAD remained at that checkpoint throughout R2.
- Initial working tree contained only the expected uncommitted R1 documents:
  `PHASE_3A_SCHEMA_AND_MIGRATION_PLAN_REPORT.md` and `docs/database/`.
- No reset, clean, checkout, amend, commit, push, PR, or deploy occurred.

## Nine R1 issues and R2 corrections

| R1 issue | R2 correction |
| --- | --- |
| Field-level schema missing | Added exact per-field catalogs for all required entities, including Django type, lengths/precision, null/blank/default/choices, related name/on-delete, mutability, index, constraint, source/backfill, and phase |
| No concurrency-safe business numbering | Added `BusinessNumberSequence`, exact namespace/period formats, PostgreSQL row-lock algorithm, three-attempt retry, idempotency, SQLite limitations, and concurrency tests |
| No named constraint catalog | Added 83 stable constraint references/definitions with expression, scope, PostgreSQL/SQLite behavior, and phase |
| No data mapping matrix | Added current/legacy source-to-target matrix with transforms, determinism, ambiguity, validation, exception handling, and phase |
| Migration review state mixed with business status | Defined only `LEGACY`/`MVP_V1` in `data_contract`; unresolved review work is an external exception report and never lifecycle state |
| Shadow lifecycle fields unnamed | Fixed quotation/order canonical field as `workflow_status`; fixed `revision`; listed every retained text/status/version compatibility field and cutoff policy |
| Legacy import depended on migration environment | Prohibited all migration access to legacy URL/files; moved import to a future separately authorized dry-run-first tool design |
| Phase 3B/3C/3D overlapped | Defined non-overlapping scope, entry/exit gate, files, compatibility, and recovery for each phase |
| Money precision/rounding unresolved | Fixed monetary Decimal(20,4), quantity Decimal(16,4), USD quantum .01, VND quantum 1, `ROUND_HALF_UP`, calculation order, DB/service boundaries, and legacy delta tolerance |

## Canonical field and status decisions

- Existing Customer and Product sources remain `BusinessCustomer` and
  `BusinessProduct`; managed `BusinessMaterial` is new.
- Customer `status` is only `ACTIVE`/`INACTIVE`; Part/Material use `is_active`.
- RFQ uses the exact Phase 2 lifecycle in `SalesRfq.status`.
- Existing `SalesQuotation.status`, `version`, and `approval_status` remain
  compatibility fields. Canonical fields are `workflow_status` and `revision`;
  decisions are separate immutable rows.
- Existing `TransactionOrder.status`, `quoted_at`, and `completed_at` remain
  compatibility fields. Canonical fields are `workflow_status`,
  `source_quotation_sent_at`, and `completed_at_v1`.
- Existing extended headers and detail rows are `data_contract=LEGACY`; new V1
  services explicitly create `MVP_V1`. No old row is auto-promoted.
- Quotation family number is stored once on the RFQ, avoiding a uniqueness rule
  that would incorrectly block R1/R2 revisions.

## Business number strategy

`BusinessNumberSequence` is unique on `(namespace, period)`: CUS/PART/MAT use
`GLOBAL`; RFQ/QT/SO use year. PostgreSQL allocation uses
`transaction.atomic()` and `select_for_update()`, then increments, formats, and
inserts under a unique business-code constraint. Integrity races retry at most
three times; gaps are allowed. Commands require idempotency key plus request
hash. Quotation revision locks the RFQ, allocates max revision + 1, and relies
on unique `(rfq, revision)`. SQLite is not accepted as concurrency evidence.

## Money contract

- Money: `DecimalField(max_digits=20, decimal_places=4)`.
- Quantity: `DecimalField(max_digits=16, decimal_places=4)`.
- Currencies: VND and USD only.
- USD quantum: `0.01`; VND quantum: `1`; rounding: `ROUND_HALF_UP`.
- Backend quantizes each line, sums quantized lines, quantizes discount/tax, and
  derives total. Client totals are not authoritative.
- DB checks scalar nonnegative/bounds and same-row header equation. Services and
  tests check rounded line equations and header-versus-child sums.
- Legacy float/text conversion uses Decimal from string and stops on missing
  currency, non-finite values, or unexplained delta above USD .01/VND 1.

## Constraint and mapping summary

The plan defines 83 referenced constraints with no undefined or unreferenced
names. It includes business-code and sequence uniqueness, RFQ/document/revision/
line/order uniqueness, positive quantity, currency/money/date bounds, effective
quotation partial uniqueness, decision uniqueness/reasons, order-source
uniqueness, progress bounds/reasons, and required audit identity.

Maker-checker, cross-parent relationships, valid transition edges, child-row
sums, date-vs-datetime comparisons, and append-only enforcement are correctly
assigned to services/permissions/tests rather than misrepresented as portable
database checks.

The mapping matrix preserves current PKs/fields, maps only deterministic values,
does not synthesize RFQs, commercial quotations, approvals, customer decisions,
accepted quotations, confirmed orders, actors, or money. Ambiguous rows remain
LEGACY and enter an exception report.

## Legacy import separation

No Django migration reads a legacy database, URL, environment variable, network,
or author-machine file. A future separately assigned command may be designed as
`import_legacy_reference_data --dry-run`; it must use explicit read-only input,
source fingerprint/checksum, collision/evidence reports, idempotent atomic
batches, resume cursor, no overwrite, and separate Owner approval for apply.
Neither R2 nor Phase 3B builds or runs it.

## Phase boundaries

- Phase 3B: BusinessNumberSequence, schema-needed permission definitions,
  Customer, Part, Material, RFQ/line/document/review, constraints/tests.
- Phase 3C: quotation header/line revisions, decisions, money, validity,
  snapshots, constraints/tests.
- Phase 3D: order/header lines, progress, audit, complete RBAC grants,
  constraints/tests.

Each phase has separate additive, deterministic validation/backfill, constraint,
and gate boundaries. No Phase 3 phase switches API/service/UI consumers.

## Verification

Commands run from `django_backend/`:

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest -q
```

Results:

- Django system check: `PASS`, 0 issues.
- Migration drift: `PASS`, `No changes detected`.
- Full backend test: `PASS`, `99 passed, 140 skipped in 1.64s`.
- Failed/errors: 0/0.
- Markdown table column check: 0 mismatches.
- Code fences: balanced.
- Constraint cross-reference: 83 references, 83 definitions, 0 missing.
- Referenced implementation paths: present.
- Frontend build was not run because no frontend file changed.

## Risk and stop controls

The plan now records lane color, probability, impact, detection, prevention,
stop condition, and recovery. Additive schema is green/yellow; backfill and
constraint activation are yellow; ambiguous legacy import and any destructive
or production mutation are red. Destructive migration, uncertain environment,
missing approval/backup, unknown mapping/status, constraint violation,
unexplained money delta, or SQLite-only concurrency evidence blocks rollout.

## Git evidence and safety confirmation

At report creation, `git diff --stat` is empty because all Phase 3A documents
are untracked; `git status --short` is the authoritative inventory. Final values
after formatting checks:

`git diff --stat`:

```text
(empty; Git does not include untracked files in this diff)
```

`git status --short`:

```text
?? PHASE_3A_SCHEMA_AND_MIGRATION_PLAN_R2_REPORT.md
?? PHASE_3A_SCHEMA_AND_MIGRATION_PLAN_REPORT.md
?? docs/database/
```

Only these documentation outputs are in scope:

- updated `docs/database/PHASE_3A_SCHEMA_AND_MIGRATION_PLAN.md`;
- preserved R1 `PHASE_3A_SCHEMA_AND_MIGRATION_PLAN_REPORT.md`;
- new `PHASE_3A_SCHEMA_AND_MIGRATION_PLAN_R2_REPORT.md`.

No model, migration, database, seed/demo data, API, serializer, permission
implementation, service, or React file changed. No SQLite/dump appeared. No
commit, push, PR, or deployment was performed.
