# Phase 6B canonical browser E2E implementation report

Date: 2026-09-17 (Asia/Tokyo)

## Verdict

`PASS_PHASE_6B_CANONICAL_BROWSER_E2E`

The canonical browser workflow completed successfully against the Phase 6
PostgreSQL/Redis/Django/Vite stack. The successful run created exactly one RFQ
for marker `PHASE6B-E2E-bee506f628`, recovered it after a hard refresh and
memory-session loss without a duplicate create, and completed the chain through
quotation acceptance and order completion. Cleanup used only the Phase 6 stop
helper; the unrelated runtime on port 8000 remained healthy and unchanged.

## Discovery gap matrix

| Workflow step | Canonical backend | Existing frontend/browser path | Enforcement and tests | Phase 6B result |
|---|---|---|---|---|
| Customer/Product | Read and command endpoints exist | RFQ canonical customer/part/material selectors exist; unrelated catalog screens remain static | Active user/role and exact permission checks; Phase 4A/4B tests | Reused selectors; added bounded fictional master fixture only |
| RFQ draft | Create/read exists | Existing RFQ workspace | Idempotency, reconciliation, DRAFT locking, sanitized errors, session reset | Preserved |
| RFQ lines | Add/update/remove/read exists | Existing RFQ workspace | Protocol/unit guard, ambiguous-result handling, lifecycle tests | Preserved; browser runner exercises add and edit |
| RFQ submit | Submit exists | Existing RFQ workspace | Sales/Admin exact permission and lifecycle checks | Preserved |
| RFQ technical review | Start/request-info/complete/decline exists | No frontend path existed | Manager-only backend and Phase 4B tests | Added canonical start/complete client and Manager UI to bridge `SUBMITTED` to `READY_TO_QUOTE` |
| Quotation create/update/submit | All exist | Existing quotation workspace | Idempotent create/revision, ownership, lifecycle, error tests | Preserved; added stable browser selectors |
| Manager approval/rejection | Both exist | Existing Manager decision UI | Exact Manager permission, maker-checker and payload tests | Preserved; browser runner executes approval; focused tests retain rejection enforcement |
| Customer accept/decline | Both exist | Existing Sales/Admin evidence UI | Exact permission, SENT lifecycle and evidence validation | Preserved; browser runner executes acceptance; focused tests retain decline enforcement |
| Conversion/order creation | Idempotent conversion exists | Existing order workspace | Exact permissions, retained key and GET-only reconciliation | Preserved; browser runner covers conversion |
| Order progress | Progress/hold/resume/complete/cancel exist | Existing order controls | Admin/Manager lifecycle matrix and ambiguous-outcome reconciliation | Preserved; browser runner covers progress, hold, resume, complete |
| Entity timeline | Canonical read exists | Existing order timeline | Entity-scoped permission/read tests | Preserved; browser runner asserts rendered evidence |
| Global audit | Canonical read exists | Existing role-gated panel | Admin/Manager only; Sales denied without request | Preserved; browser runner asserts Sales denial and Manager evidence |
| Session switching | Memory-only auth exists | RFQ reset existed; quotation/order retained mutable local state | RFQ Phase 5C tests | Added explicit quotation/order attempt reset and complete local-state reset |
| Browser automation | Selenium smoke precedent and local Chrome/Selenium exist | No Phase 6B runner | None | Added a dedicated Selenium runner without adding a frontend dependency |

## Files changed for Phase 6B

- `figma_make_frontend/src/App.tsx`
- `figma_make_frontend/src/api/rfq.ts`
- `figma_make_frontend/src/api/rfqCommands.ts`
- `figma_make_frontend/src/api/quotationCommands.ts`
- `figma_make_frontend/src/api/orderCommands.ts`
- `figma_make_frontend/src/api/phase6b.test.ts`
- `figma_make_frontend/src/components/RfqWorkspace.tsx`
- `figma_make_frontend/src/components/QuotationWorkspace.tsx`
- `figma_make_frontend/src/components/OrderWorkspace.tsx`
- `figma_make_frontend/package.json`
- `figma_make_frontend/phase6.config.test.ts`
- `django_backend/apps/api/services/canonical_read_service.py`
- `django_backend/apps/core/management/commands/phase6b_e2e_fixture.py`
- `django_backend/apps/core/tests/test_phase6b_e2e_fixture.py`
- `tests/e2e/phase6b_canonical_browser_e2e.py`
- `docs/phase6/PHASE_6B_BROWSER_E2E.md`
- `docs/phase6/LOCAL_FULL_STACK.md`
- `scripts/phase6/Start-Phase6.ps1`
- `PHASE_6B_CANONICAL_BROWSER_E2E_IMPLEMENTATION_REPORT.md`

No migration, Compose definition, legacy write boundary, or unrelated UI file
was changed. The Phase 6 launcher received one bounded repair so live validation
always builds the current Django source before migration/startup.

## Implemented workflow and correctness changes

1. Added fail-closed RFQ review response validation plus exact canonical
   `review/commands/start/` and `review/commands/complete/` transports.
2. Added Manager-only review controls. Completion derives feasible line IDs
   from the authoritative loaded RFQ lines and explicitly confirms lines where
   drawings are not required. Backend remains authoritative for all technical
   evidence checks.
3. Added Sales/Admin authoring locks so Manager cannot edit/create RFQs in the
   UI while retaining read/review access.
4. Added `reset()` to quotation-create and order-conversion attempt managers.
   Unauthenticated transitions abort requests, invalidate generations, clear
   selected data/forms/evidence, release gates, and discard retained
   idempotency context. No old logical attempt can cross a user session.
5. Added an explicit logout path in the Sales workflow for role switching.
6. Added stable, non-sensitive DOM selectors for browser automation. No token,
   idempotency key, password, backend exception, or raw audit metadata is
   rendered.

## Fictional fixture and data contract

The idempotent fixture creates exactly three local-only users and three master
records:

- `phase6b.admin@example.invalid`, `phase6b.sales@example.invalid`,
  `phase6b.manager@example.invalid`;
- `CUS-PHASE6B-E2E` — `Phase 6B Fictional Robotics`;
- `MAT-PHASE6B-E2E` — `Phase 6B Fictional SUS304`;
- `PART-PHASE6B-E2E` — `Phase 6B Fictional Precision Bracket`.

The password is read from stdin and never accepted as a command argument,
printed, committed, or stored by the runner. Workflow entities are created only
through browser calls to canonical APIs and use project prefix
`PHASE6B-E2E-<random suffix>`.

Canonical orders/progress/audit are deliberately immutable and append-only, so
no cleanup command bypasses domain protection. The contract does not authorize
physical deletion of those workflow records; they remain bounded and visibly
fictional.

## Live defects found and bounded repairs

The live run demonstrated the following concrete defects. No speculative
refactor was made:

1. The launcher reused a stale Django image, so the new fixture command was not
   present. `Start-Phase6.ps1` now builds the current Django source before
   dependency checks and migrations; a focused Phase 6A config test fixes the
   ordering contract.
2. Hash navigation changed the URL but not the already-mounted App route.
   `App.tsx` now synchronizes route state on `hashchange` while preserving the
   intentionally memory-only authenticated session.
3. Selenium text entry into native date controls was locale-dependent. The
   runner now uses the native input value setter and dispatches `input` and
   `change`, then asserts the assigned value.
4. Canonical RFQ detail responses legitimately use `compatibility: null`, but
   the frontend protocol guard rejected it after a successful create. The RFQ
   read contract now accepts only an object or `null`; it does not weaken any
   write payload validation.
5. The quotation-family read included RFQs whose family number was SQL `NULL`.
   The canonical read service now excludes both `NULL` and empty family
   numbers, with a parameterized backend regression test.
6. Quotation and order browser steps could observe matching list/local text
   before authoritative detail reconciliation. Stable non-sensitive detail
   state attributes were added, and the runner now waits for exact backend-
   reconciled status/progress before continuing.

## Browser runner evidence

The Selenium runner proved:

- login and canonical selector loading;
- RFQ create, hard browser refresh, memory-session loss, re-login, and exact
  single-RFQ recovery (no duplicate create);
- line add/edit and RFQ submit;
- Manager technical review to `READY_TO_QUOTE`;
- quotation create/submit and Manager approval;
- send/customer acceptance;
- idempotent conversion;
- progress, hold, resume, complete;
- Sales global-audit denial plus Manager timeline/global audit evidence;
- role switching without inheriting mutable workspace state.

Successful terminal evidence:

`PHASE6B_CANONICAL_BROWSER_E2E_PASS project=PHASE6B-E2E-bee506f628 rfq=RFQ-2026-0006 order=SO-2026-0003`

Rejection and customer-decline branches remain covered by existing Phase 5D
behavioral transport/lifecycle tests and Phase 4C backend command tests. They
cannot both be followed by conversion in one quotation chain: backend allows a
new revision only from `REJECTED`, while `DECLINED` is terminal for that family.

## Validation evidence

### Frontend

- `test:phase5a`: 12 passed.
- `test:phase5b`: 18 passed.
- `test:phase5c`: 34 passed.
- `test:phase5d`: 22 passed.
- `test:phase5e`: 38 passed.
- `test:phase6a`: 5 passed.
- `test:phase6b`: 8 passed.
- full `pnpm run test`: 137 passed, 0 failed.
- `pnpm run typecheck`: passed.
- `pnpm run typecheck:phase5a`: passed.
- `pnpm run build`: passed (25 modules transformed).
- Phase 6A formatter check: passed.
- targeted formatter check for all modified frontend source/test files: passed.
- Selenium runner Ruff lint and format checks: passed.

### Backend

- `python manage.py check`: passed, 0 issues.
- `python manage.py makemigrations --check --dry-run`: passed, no changes.
- focused Phase 4A–4D canonical plus Phase 6B fixture tests: 60 passed,
  8 PostgreSQL-only concurrency tests skipped under the local SQLite test run.
- Phase 6A legacy-write-boundary tests: 9 passed.
- Phase 6B fixture test independently: 1 passed.
- Ruff lint/format and Python compile checks for Phase 6B files: passed.
- Final focused fixture/canonical-read regression: 19 passed.
- Full repository pytest: 541 passed, 8 failed, 5 setup errors. All 13
  non-passing legacy-suite cases depend on the absent
  `backend/database/mecprecision.sqlite`/legacy DB alias or migration-seeded
  legacy records. Focused canonical/Phase 6 tests pass and the failures do not
  touch Phase 6B code.

## Live preflight and startup evidence

- Full read-only Docker/container/network/volume/listener preflight was
  repeated on 2026-09-17 (Asia/Tokyo).
- Docker Desktop was running; context `desktop-linux`; client/server version
  `29.4.3`, API `1.54`, Docker Desktop `4.74.0`.
- Host ports `8001` and `8443` had no Windows listener and no Docker publisher
  before startup. No alternate port was selected.
- Unrelated baseline container `mecprecision-vietnam-web-1` was healthy on
  port 8000 with ID
  `dfd724919eb2d12cb6d823cfeb8993478efe286b1f042edbdd15fc435a1d3452`,
  start time `2026-09-17T12:20:54.424692074Z`, and restart count 0.
- `Start-Phase6.ps1 -DjangoPort 8001` started only the Phase 6 project.
  PostgreSQL, Redis, and Django were healthy; Django published only
  `127.0.0.1:8001->8000`. PostgreSQL and Redis remained internal-only. Vite was
  reachable at `127.0.0.1:8443`.
- Direct Django `/api/v1/phase6/live/` and `/ready/` returned 200. The same
  endpoints returned 200 through the Vite root-relative `/api` proxy, and the
  Vite root returned 200.
- Migration check passed. Runtime database evidence reported PostgreSQL as the
  active Django database vendor/engine and Redis as the configured cache.

## Fixture and idempotency evidence

- The fixture password was generated in process, supplied only through stdin,
  never placed in an argument, file, report, or console output, and cleared
  after the run.
- Two consecutive fixture applications returned the same three user/master
  identities and the same `customer_id=1`, `material_id=1`, and `part_id=1`.
- The successful browser marker has exactly one RFQ and exactly one
  `rfq.created` audit action. Hard refresh, loss of the in-memory token,
  re-login, and RFQ recovery issued no duplicate RFQ create.

## PostgreSQL lifecycle, timeline, and authorization evidence

- Project marker: `PHASE6B-E2E-bee506f628`.
- RFQ: exactly one, ID 6, `RFQ-2026-0006`, `MVP_V1`, final state `CLOSED`, one
  line, two technical-review records (start and completion).
- Quotation: exactly one, ID 5, `QT-2026-0005-R0`, `MVP_V1`, final state
  `ACCEPTED`, one line, approval `APPROVED`, customer decision `ACCEPTED`.
- Order: exactly one, ID 3, `SO-2026-0003`, `MVP_V1`, final state `COMPLETED`,
  progress 100, one item, source RFQ 6 and source quotation 5.
- The five order events were: creation to `CONFIRMED` at 0; progress to
  `IN_PROGRESS` at 40; hold to `ON_HOLD` at 40; resume to `IN_PROGRESS` at 40;
  completion to `COMPLETED` at 100.
- Exact entity-pair audit filtering returned the expected 16 actions: RFQ
  create/update/submit/review, quotation create/submit/approve/send/accept, and
  order convert/progress/hold/resume/complete.
- The UI proved the entity timeline and Manager global audit evidence. It also
  proved Sales denial without issuing the global-audit request. A separate live
  Sales request to the canonical global-audit endpoint returned 403.
- Rejection and decline remain covered by focused frontend/backend tests. They
  were not applied to the successful chain because either terminal branch
  would make conversion impossible.

Defect-isolation runs created a bounded number of additional fictional
`PHASE6B-E2E-*` append-only records before the final pass. They were not deleted
or rewritten because canonical audit/workflow records are immutable. They are
separate markers and do not weaken the exact-one-RFQ evidence for the successful
marker.

## Cleanup and coexistence evidence

- Cleanup ran only `Stop-Phase6.ps1`.
- No Phase 6 container or network remained; host ports 8001 and 8443 were free.
  The named Phase 6 PostgreSQL and media volumes were preserved.
- The unrelated Compose project still reported `running(5)`.
- `mecprecision-vietnam-web-1` retained the exact baseline ID, image, start
  time, published port 8000, restart count 0, and healthy state.
- No prune, Docker Desktop restart, WSL shutdown, unrelated stop/remove,
  deployment, stage, commit, push, reset, clean, or stash occurred.
- PowerShell parser validation and `git diff --check` passed. The latter emitted
  only existing LF-to-CRLF working-copy warnings and no whitespace errors.

## Security and scope confirmation

- Django remains the sole application backend.
- All new workflow calls use canonical `/api/v1/canonical/...` routes.
- No legacy MVP mutation route was added or used.
- No token/password/idempotency key persistence or logging was introduced.
- Exact role/lifecycle/backend checks remain authoritative.
- No migration, secret, external automation, AI/OCR, Phase 6C, deployment, or
  unrelated Docker change was introduced.
- Nothing was staged, committed, pushed, reset, cleaned, or stashed.

`PASS_PHASE_6B_CANONICAL_BROWSER_E2E`
