# Phase 5 Scope Discovery and Implementation Plan

## Owner designation and revised verdict

On 2026-09-13, the Owner designated the current MVP continuation after
`27002cbf830285f261dda91f1e8b39cd6d72ed3b` as **Phase 5 — React Frontend
Integration with the Canonical API**. This designation moves the frontend work
previously numbered Phase 6 in the MVP specification into the current Phase 5
sequence. Historical CRM migration, Business UI, and AI Factory uses of the
same phase number remain historical and are not part of this sequence.

The Owner also authorized **Phase 5A — Canonical Frontend Transport and
Authentication Foundation** as the first independently testable subphase.
Phase 5A is limited to a typed, bounded canonical HTTP transport, injectable
in-memory Bearer authentication, canonical envelope parsing/error mapping, and
focused tests. Business-screen integration remains outside Phase 5A.

The earlier discovery verdict is resolved by this designation. The evidence
and historical conflict analysis below are retained to explain why the Owner
decision was necessary and which old phase labels are superseded.

## Initial repository state

| Item | Verified value |
| --- | --- |
| Working directory | `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO` |
| Git root | `C:/Users/hoang/Documents/ChatGPT/WEB Ô TÔ DJANGO` |
| Repository | `Django-web-t-123` |
| Remote | `https://github.com/hoangquocquan/Django-web-t-123.git` |
| Branch | `codex/demo-database-validation` |
| HEAD | `27002cbf830285f261dda91f1e8b39cd6d72ed3b` |
| Subject | `phase4d: add order progress audit command APIs` |
| Parent | `86e2a0f669acd05764ab05bdf1ec7c64524cab16` |
| Initial status | Clean |

The baseline exactly matched the task checkpoint, so discovery was allowed to
continue.

## Evidence reviewed

The discovery reviewed the canonical root README, the Phase 1/2 contract
history, the Phase 3A planning material, all required Phase 3B through Phase 4D
reports, the canonical business specification, migration roadmaps and Phase 5
status/prompt documents, the project handover, the canonical API boundary,
frontend structure/data sources, test configuration, and recent Git history.

Required reports reviewed in full:

- `PHASE_3B_POSTGRESQL_VALIDATION_FINAL_REPORT.md`
- `PHASE_3C_QUOTATION_IMPLEMENTATION_REPORT.md`
- `PHASE_3D_ORDER_PROGRESS_AUDIT_IMPLEMENTATION_REPORT.md`
- `PHASE_4A_CANONICAL_READ_API_IMPLEMENTATION_REPORT.md`
- `PHASE_4B_MASTER_DATA_RFQ_COMMAND_API_IMPLEMENTATION_REPORT.md`
- `PHASE_4C_QUOTATION_ORDER_CONVERSION_COMMAND_API_IMPLEMENTATION_REPORT.md`
- `PHASE_4D_ORDER_PROGRESS_AUDIT_API_AND_WRITE_BOUNDARY_REPORT.md`

## Evidence defining—and failing to define—Phase 5

### Current MVP sequence

1. `PHASE_2_BUSINESS_DOMAIN_CONTRACT_REPORT.md:115-116` explicitly assigns the
   work split to Phase 3 database/domain, Phase 4 API, and **Phase 6 frontend**.
2. `docs/business/MINI_ENTERPRISE_BUSINESS_SPEC_V1.md:659-694` repeats that
   mapping: Phase 3 is persistence, Phase 4 is API/domain commands, and Phase 6
   binds React to the Phase 4 APIs and implements the required UI states.
3. The same specification identifies the present React app as hard-coded and
   without an API client/fetch call at lines 608-619, then assigns individual UI
   capabilities to Phase 6 in the gap matrix at lines 625-639.
4. `PHASE_3D_ORDER_PROGRESS_AUDIT_IMPLEMENTATION_REPORT.md:360` recommends
   Phase 4 API/service adapters **and frontend integration**, but does not define
   a Phase 5 or split frontend work into a Phase 5 subphase.
5. Phase 4A through 4D implemented the canonical API boundary. Phase 4A states
   that no frontend binding was implemented (`PHASE_4A...REPORT.md:208`), Phase
   4C explicitly excludes frontend work (`PHASE_4C...REPORT.md:9-10`), and Phase
   4D ends only with the label `READY_FOR_PHASE_5`
   (`PHASE_4D...REPORT.md:5`). Phase 4D provides no Phase 5 objective, scope,
   paths, contracts, or acceptance test.

Therefore `READY_FOR_PHASE_5` proves sequencing readiness only; it does not
define what Phase 5 is.

### Competing historical meanings

The repository contains at least four incompatible meanings or states:

| Evidence | Meaning/status |
| --- | --- |
| `docs/migration/MIGRATION_ROADMAP.md:41-46` | Phase 5 is completed CRM migration; Phase 5.1 is completed CRM hardening. |
| `docs/codex-prompts/PHASE_5_CRM_MIGRATION.md:1-27` | Phase 5 is read-only legacy CRM ORM/repository/service work with no contact write API. |
| `docs/handover bàn giao dự án/MEC_PRECISION_PROJECT_HANDOVER.md:210-220` | Phase 5 is Business UI and is already complete with QA warnings. |
| `docs/handover bàn giao dự án/MEC_PRECISION_PROJECT_HANDOVER.md:407-415` | A later roadmap reuses Phase 5 for AI Software Factory expansion. |
| `docs/migration/future-phases/PHASE_5_STATUS.md:1-9` | Phase 5 is `PLANNED`, but both objective and dependencies are `TBD`. |

These documents predate or describe different phase systems and cannot safely
be imported into the current Phase 3/4 MVP sequence. Selecting any one would
contradict another durable repository source.

## Current architecture and data-flow map

```text
React/Vite prototype (figma_make_frontend/src/App.tsx)
  - local hard-coded arrays and presentation-only login/forms/actions
  - no fetch/API client, token/session adapter, or server-state layer
  - unused additional mocks in src/data/mock.ts
                         X  no binding exists
                         |
                         v
/api/v1/canonical/
  Foundation Bearer authentication
  -> active canonical role
  -> exact non-wildcard view + command permissions
  -> strict request serializers
  -> canonical read/command services
  -> Phase 3 domain operations, row locks, atomic transactions
  -> canonical models + append-only AuditEvent/OrderProgressEvent evidence

Legacy endpoints and Django/server-rendered UI remain compatibility surfaces;
they must not be treated as the canonical React data source or allowed to
mutate protected MVP_V1 records.
```

## Existing contracts that any approved future scope must preserve

These are established constraints, not a definition of Phase 5:

- Canonical route namespace: `/api/v1/canonical/`.
- Success envelope: `{"success": true, "data": ...}`.
- Sanitized error envelope with stable machine code and optional safe details.
- Foundation Bearer authentication; active user and active canonical role.
- Exact action and visibility grants; wildcard-only permissions remain denied.
- Canonical Admin/Sales/Manager role and ownership/maker-checker boundaries.
- Uppercase canonical states, ISO-8601 aware datetimes, and Decimal values as
  strings.
- Backend/domain services remain authoritative for money, numbering,
  transitions, idempotency, locking, transactions, and audit evidence.
- No frontend mock may silently replace canonical server data.
- Legacy records/routes remain compatible and cannot mutate protected MVP_V1
  records through a bypass.
- No database migration is justified by the currently discovered evidence.

## Scope conclusion

The repository does **not** prove whether the next Phase 5 concerns frontend
integration, backend continuation, authentication, reporting, deployment, AI
Factory expansion, CRM migration, or another workstream. Frontend integration
is the most plausible next product gap, but the authoritative MVP contract
labels it Phase 6, and neither a first screen nor an authentication/session
strategy is selected. That inference is insufficient authorization to modify
the frontend.

Consequently the following cannot be established without Owner direction:

- exact Phase 5 objective and phase-number relationship to the documented
  Phase 6 frontend work;
- first independently testable subphase;
- in-scope/out-of-scope feature boundary;
- expected implementation and test paths;
- required API subset and UI workflow;
- browser authentication/token storage and CSRF contract;
- detailed permission/ownership behavior per screen;
- compatibility/cutover rule for prototype mocks and legacy UI;
- loading, empty, success, validation, permission-denied, conflict, and server
  error acceptance criteria.

## Candidate implementation plan after the decision

After an authoritative Phase 5 specification is designated, a new task should:

1. Reconfirm this checkpoint or the Owner-approved successor checkpoint.
2. Record the authoritative objective, exact first subphase, changed paths, and
   acceptance matrix before editing.
3. Implement only that subphase using `/api/v1/canonical/`, without duplicating
   backend business rules or silently falling back to mock data.
4. Add focused tests for authentication, exact permissions, successful data
   flow, validation, forbidden, conflict, server-error, loading, and empty
   states that are applicable to the selected surface.
5. Run configured compiler/build checks, relevant Phase 3/4 preservation suites,
   and `git diff --check`. Run Django/model or PostgreSQL validation only if the
   approved scope actually changes those boundaries.
6. Produce the Owner-designated subphase implementation report with the
   required implementation evidence. For Phase 5A this is
   `PHASE_5A_CANONICAL_FRONTEND_FOUNDATION_IMPLEMENTATION_REPORT.md`.

## Owner decision resolution

The previously requested decision has been supplied. Phase 5A may proceed only
within the acceptance boundary recorded above. The implementation and exact
validation evidence are recorded in
`PHASE_5A_CANONICAL_FRONTEND_FOUNDATION_IMPLEMENTATION_REPORT.md`.

Phase 5B is not authorized by this decision.

## Original discovery validation snapshot

- `git diff --check`: passed.
- Runtime tests were not run during discovery; discovery changed documentation only and the
  stop rule prohibits speculative Phase 5 implementation.
- Docker/PostgreSQL: not used; no database-specific behavior changed.
- Tracked diff stat at discovery closure: empty because the sole artifact was
  untracked.
- Git status at discovery closure:
  `?? PHASE_5_SCOPE_DISCOVERY_AND_IMPLEMENTATION_PLAN.md`.
- Final branch/HEAD/subject/parent remain exactly the verified initial values.
- The plan file's SHA256 is intentionally reported in the task handoff rather
  than embedded here, because embedding a file's digest changes that digest.
