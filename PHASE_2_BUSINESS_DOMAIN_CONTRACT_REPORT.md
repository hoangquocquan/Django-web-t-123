# Phase 2 Business Domain Contract Report

## Verdict

`PASS`

Phase 2 produced a code-evidenced business source of truth for the portfolio MVP
without implementing Phase 3. The contract is sufficient to design the database
without guessing the core workflow.

Conclusion: `READY_FOR_PHASE_3`.

## Repository baseline

- Task: `DJANGO-PHASE-2-BUSINESS-DOMAIN-CONTRACT-V1`
- Branch: `codex/demo-database-validation`
- Base commit: `df14dc510fee53189bfd70fe0d9aa9fb2de7c7d0`
- Root `AGENTS.md`: not present.
- Canonical backend/frontend: `django_backend/` and `figma_make_frontend/`.
- Working tree before Phase 2 contained the preserved, valid uncommitted Phase 1
  work shown below. Phase 2 did not reset, overwrite, or delete it.

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

## Inventory performed

The read-only inventory covered:

- Managed and unmanaged models in foundation, business core, CRM, catalog,
  sales, transaction domain, knowledge, and related modules.
- Status constants, service methods, validation, financial calculation,
  transition behavior, and audit writes.
- DRF serializers, views, URL routing, authentication, permission checks, and
  foundation permission seeds.
- Backend tests relevant to customer/product, legacy RFQ data, quotations,
  orders, workflow, upload, authorization, and compatibility.
- Django `admin_ui` and `business_ui` views/templates and their actual ORM data
  sources.
- React `App.tsx`, its local hard-coded arrays/screens/actions, and the separate
  unused `src/data/mock.ts` exports.

The primary evidence paths are cited directly in
`docs/business/MINI_ENTERPRISE_BUSINESS_SPEC_V1.md` and summarized in its gap
matrix.

## Business conflicts found

1. **Duplicate ownership:** managed BusinessCustomer/BusinessProduct coexist
   with unmanaged legacy Customer/Product; Material has no managed master.
2. **RFQ terminology and ownership:** legacy QuoteRequest is read-only and is
   exposed as “quotes”; no managed RFQ header/line/document source exists.
3. **Missing technical review:** no canonical entity, decision, or transition
   contract exists.
4. **Quotation mismatch:** managed quotation is opportunity/customer based, not
   RFQ based; revision-family uniqueness, currency, tax, validity, sent
   snapshots, rejection, expiry, supersession, and customer-decision evidence
   are missing or inconsistent.
5. **Approval weakness:** current approval method allows draft/review approval
   without maker-checker comparison; Business UI requests `sales:approve`, but
   reviewed permission migrations seed only sales read/write.
6. **Order mismatch:** current order can be created directly from customer/items,
   has no accepted-quotation source/unique conversion constraint, uses `ORD-*`,
   and has noncanonical statuses.
7. **Workflow approval conflict:** order transition code may record requester and
   reviewer as the same actor and is not quotation manager approval.
8. **Fragmented audit:** TransactionHistory, OrderStatusHistory, SalesActivity,
   and CRM timeline are useful but do not form one complete immutable audit
   contract with stable actor/status/reason fields.
9. **Upload mismatch:** generic KnowledgeDocument upload/version capability is
   not linked to RFQ/RFQ line; legacy QuoteFile is metadata-only/read-only.
10. **UI truth gap:** Django templates use real data for some managed features,
    but remain partial. The canonical React app contains no API fetch and uses
    hard-coded customers, quotations, orders, dashboards, progress, login, and
    RFQ confirmation. Its additional mock data file is currently unused.

These conflicts are disclosed as `CONFLICT`, `PARTIAL`, or `MISSING`; none is
represented as complete merely because a similarly named file/screen exists.

## Decisions finalized

- Exact end-to-end flow: Customer → RFQ → Technical Review → Quotation →
  Manager Approval → Customer Decision → Sales Order → Progress → Completion.
- MVP and deferred boundaries; extended ERP/MES/AI work is explicitly excluded.
- Canonical roles Admin, Sales, Manager; Manager doubles as technical reviewer.
- Action-level permission matrix and maker-checker rule based on stable user ID.
- RFQ, Quotation, and Sales Order state machines, actors, preconditions, locks,
  reasons, and terminal states.
- Business identifiers (`CUS`, `PART`, `MAT`, `RFQ`, `QT-…-R0`, `SO`) are
  separate from internal database IDs.
- Backend-only Decimal quotation formula, ISO 4217 currency, validity and
  immutable commercial snapshots.
- One accepted quotation revision creates at most one sales order atomically.
- Timezone-aware datetimes, ISO 8601 API representation, controlled units, and
  archive/no-hard-delete policies.
- Append-only audit event requirements and secure versioned RFQ document rules.
- Error semantics and happy/negative acceptance scenarios.
- Canonical source decisions and work split for Phase 3 database, Phase 4 API,
  and Phase 6 frontend.

## Files created by Phase 2

- `docs/business/MINI_ENTERPRISE_BUSINESS_SPEC_V1.md`
- `PHASE_2_BUSINESS_DOMAIN_CONTRACT_REPORT.md`

No pre-existing file was modified by this Phase 2 task.

## Consistency and regression checks

- Referenced-code path validation: PASS; all 15 explicitly checked source paths
  exist.
- Required-section validation: PASS; all 16 required document groups present.
- Canonical-state validation: PASS; all 20 RFQ/Quotation/Order state tokens are
  present.
- Diagram/transition review: PASS. Every diagram transition has a matching table
  row; no transition-table state falls outside its entity's defined state set.
- Permission/transition review: PASS. Sales cannot perform technical review or
  approval; Manager cannot edit draft business content; Admin does not bypass
  Manager approval; all commands retain service-side authorization.
- Money review: PASS. One canonical formula is stated and used consistently:
  subtotal is the sum of quantity × unit price; discount is bounded by subtotal;
  total is subtotal − discount + nonnegative tax and cannot be negative.
- Gap matrix review: PASS. Every required capability has current model/API/UI/test
  evidence, status from the permitted vocabulary, and a Phase 3/4/6 or deferred
  action.
- Full backend test: PASS — `99 passed, 140 skipped in 1.33s`; `0 failed`,
  `0 errors`. All skips remain the previously classified missing legacy artifact
  lane.
- Migration drift: PASS — `No changes detected`.
- No legacy database was run, created, copied, seeded, or modified.

## Current cumulative Git diff

The tracked diff below includes preserved Phase 1 changes. New untracked Phase 2
documents do not appear in `git diff --stat` until tracked.

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
?? PHASE_2_BUSINESS_DOMAIN_CONTRACT_REPORT.md
?? django_backend/tests/test_project_stabilization.py
?? docs/business/
```

## Safety confirmations

- Phase 2 changed documentation only.
- No code, model, migration, serializer, view, URL, permission, API, React UI,
  seed, database, or business data was changed by this task.
- No legacy module was deleted and no AI capability was added.
- No commit, push, pull request, deployment, or production action occurred.
- Phase 3 was not started.

## Phase 3 priorities

1. Establish canonical managed Material, RFQ/line/document/review, quotation
   revision/decision, order source/snapshot, and AuditEvent persistence.
2. Evolve BusinessCustomer and BusinessProduct as canonical Customer/Part with
   business codes and required invariants.
3. Add exact enum choices and database constraints for codes, revision
   uniqueness, positive quantities/money, and one-order conversion.
4. Design migrations that preserve existing managed and legacy references; do
   not normalize or import data without a separately approved data plan.
5. Add domain-level tests for every state transition, invariant, permission
   separation, concurrency case, and negative acceptance scenario before Phase 4.

The project is `READY_FOR_PHASE_3` from a business-contract perspective.
