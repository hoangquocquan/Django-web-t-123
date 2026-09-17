# Phase 6 Scope Discovery and Release Plan

> Historical planning baseline: implementation status in this document records
> the pre-Phase 6 discovery point. Current results are authoritative only in the
> Phase 6A-D validation reports and the Phase 6E final checkpoint report.

## 1. Final verdict

`READY_FOR_PHASE_6A`

The Owner has resolved the Phase 6 product scope: this is a portfolio/demo application that must behave as closely to a production system as reasonably possible. The Phase 3–5 canonical backend and RFQ/quotation/order React workspaces are the baseline. Phase 6 must close the proven integration, canonical master-data, RFQ-review, legacy-write, browser automation, PostgreSQL, static-delivery, security, CI, backup/restore, rollback, UAT, and operating-documentation gaps.

The exact Phase 6 sequence is now independently testable and may begin with a separately authorized Phase 6A task. This discovery task itself does not implement Phase 6A. The target verdict after successful Phase 6E is `READY_FOR_PORTFOLIO_PRODUCTION_DEMO`.

### Authoritative Owner scope incorporated

The in-scope runtime is React/Vite → Django canonical API → PostgreSQL, with production-like settings/security and isolated container resources where justified. The required demonstrable chain is Customer/Product → RFQ draft/lines/submission → quotation creation/submission → approval or rejection → accepted quotation conversion → order progress lifecycle → entity timeline → global audit.

AI, OCR, chatbot, forecasting, n8n, Zalo, AI FACTORY, external automation, real payments, unrelated product expansion, microservices, and a second application backend are excluded until Phase 6 is complete. Django remains the sole application backend. A static web/reverse-proxy process is permitted only as delivery infrastructure, not as a second backend.

## 2. Repository and baseline verification

| Gate | Evidence | Result |
|---|---|---|
| Project root | `git rev-parse --show-toplevel` returned `C:/Users/hoang/Documents/ChatGPT/WEB Ô TÔ DJANGO` | PASS |
| Repository identity | `origin` fetch/push is `https://github.com/hoangquocquan/Django-web-t-123.git` | PASS |
| Branch | `codex/demo-database-validation` | PASS |
| HEAD | `01f15037e64d6c565e8444dc99eee6c9eb7c37f4` | PASS |
| Subject | `phase5e: repair progress reconciliation evidence matching` | PASS |
| Staged state | `git diff --cached --name-status` returned empty | PASS |
| Initial worktree | `git status --short` returned empty | PASS |

The repository name in the task is the Git remote identity; it is not a child directory beneath the declared project root.

## 3. Evidence sources and method

Reports were treated as leads and reconciled with current source. No runtime claim below is based only on an old report.

Primary current-code evidence:

- Canonical ownership and entrypoints: `README.md:3-23`.
- Backend routing: `django_backend/config/urls.py:6-14`, `django_backend/apps/api/urls.py:89-91`, and `django_backend/apps/api/canonical_urls.py:77-380`.
- Environment settings: `django_backend/config/settings/base.py:95-196,205-261,308-321`; `development.py:6-9`; `production.py:24-104`; `test.py:6-23`.
- Authentication: `django_backend/apps/api/authentication.py:9-27`; `django_backend/apps/foundation/services.py:109-245`; `django_backend/apps/foundation/models.py:26-68,113-150`; `django_backend/apps/api/views/foundation.py:66-118`.
- Canonical authorization: `django_backend/apps/api/canonical_permissions.py:7-46,59-126`.
- Domain data: `django_backend/apps/business_core/models.py:26,70,138,249`; `django_backend/apps/sales/models.py:227,519,665,716,868,980,1027,1119`; `django_backend/apps/transaction_domain/models.py:107-143,339-373,555,607`.
- Canonical command delegation: `django_backend/apps/api/services/canonical_command_service.py:22-55,173-369,497-943,946-1009,1081-1283`.
- Legacy write surfaces: `django_backend/apps/api/views/business_core.py:59-164`; `django_backend/apps/api/views/transaction_domain.py:55-125`; `django_backend/apps/api/views/admin_interface.py:144-247,338-428`; `django_backend/apps/business_core/services.py:36-131`.
- Frontend transport/authentication: `figma_make_frontend/src/api/canonical.ts:1-3,43-108,243-369`; `foundation.ts:184-215,303-442`; `App.tsx:98-105,1543-1689`.
- Frontend feature wiring: `App.tsx:1278-1461`; `RfqWorkspace.tsx:344-463`; `QuotationWorkspace.tsx:463-532,848-1004`; `OrderWorkspace.tsx:214-244,320-498,693-831`.
- Prototype data still in the canonical React application: `App.tsx:31-71,1319-1386`.
- Frontend scripts and test inventory: `figma_make_frontend/package.json:6-18`.
- Vite server: `figma_make_frontend/vite.config.ts:9-41`.
- Container/static topology: `Dockerfile:15-43`; `docker-compose.yml:1-120`; `nginx/nginx.conf:1-30`.
- CI: `.github/workflows/ci.yml:7-73`; `.github/workflows/test_pipeline.yml:12-51`.
- Health and logging: `django_backend/apps/core/views.py:54-88`; `django_backend/apps/common/middleware.py:14-83`; `django_backend/apps/common/logging.py:9-36`; `django_backend/apps/common/observability.py:122-230`.
- Operations/security documentation: `docs/runbooks/RESTORE.md:1-7`; `docs/runbooks/ROLLBACK.md:1-7`; `docs/runbooks/INCIDENT_RESPONSE.md:1-7`; `docs/security/SECRETS_MANAGEMENT_POLICY.md:3-84`.

Secondary leads reviewed include all Phase 3B–3D, Phase 4A–4D, Phase 5A–5E implementation reports, Phase 5 independent review/repair reports, checkpoint/handoff reports, and current Git history. Important corroboration includes PostgreSQL closure (`PHASE_3B_POSTGRESQL_VALIDATION_FINAL_REPORT.md:48-64`), Phase 4D write-boundary analysis (`PHASE_4D_ORDER_PROGRESS_AUDIT_API_AND_WRITE_BOUNDARY_REPORT.md:149-175`), the absence of a browser framework (`PHASE_5B_INDEPENDENT_REVIEW_AND_REPAIR_REPORT.md:166`), and the final 120/120 frontend unit/contract result (`PHASE_5E_INDEPENDENT_REVIEW_AND_REPAIR_REPORT.md:124-138`). These are historical results, not tests rerun by this discovery.

## 4. Current architecture map

| Layer | Canonical path | Current behavior | Release implication |
|---|---|---|---|
| Browser | `figma_make_frontend/src/main.tsx` → `App.tsx` | React 19/Vite, hash routing, public/admin/sales prototype in one large component | Only the sales quotation slice is canonical; many neighboring screens remain prototypes |
| API transport | `src/api/canonical.ts` and `foundation.ts` | Bounded `fetch`, strict canonical namespace, JSON envelope validation, memory-only Bearer token | Good transport foundation; no session recovery/refresh or browser E2E proof |
| Django API | `/api/v1/canonical/` | Exact action permissions, canonical reads and explicit commands | Correct business boundary for Phase 6 |
| Domain | business core, sales quotation/RFQ, transaction order domain | Atomic services, lifecycle checks, snapshots, append-only evidence, PostgreSQL locks | Proven by focused source/tests and historical PostgreSQL runs |
| Persistence | PostgreSQL for production; SQLite fallback for development/test | Production fails closed unless PostgreSQL and Redis configuration is supplied | PostgreSQL must be the integrated/UAT authority |
| Legacy compatibility | `/api/v1/admin/*`, `/business/*`, `/orders/*`, `/workflows/*`, old frontend/backend trees | Still routed and some routes are writable | Must be contained before UAT so canonical records cannot be mutated outside canonical commands |
| Delivery | Django/Gunicorn image with WhiteNoise for Django static | React source/dist is not copied into the image; Compose has no frontend service | Production React delivery is absent |
| Operations | basic health, protected operations health/metrics, JSON production logs, backup/restore scripts/runbooks | Valuable foundations, but no Phase 6 staging drill or release pipeline evidence | Needs environment-specific verification and Owner/operator handoff |

## 5. Frontend-to-API-to-domain-to-database flow

| User action | Frontend call | Canonical API | Domain/service | Database evidence |
|---|---|---|---|---|
| Login | `foundation.login()` | `POST /api/v1/foundation/auth/login/` | `FoundationAuthService.login` | hashed password check; hashed token metadata, expiry, login attempt |
| Customer/part/material selectors | canonical client reads | `GET customers/`, `parts/`, `materials/` | `CanonicalReadService` | `BusinessCustomer`, `BusinessProduct`, `BusinessMaterial` MVP rows |
| RFQ draft/lines/submit | `rfqCommands.ts` | create/update/line/submit commands | `MasterDataCommandService`, `RfqCommandService` | RFQ, lines, audit events, idempotency pair |
| RFQ technical review | no current React action | start/request-information/complete/decline commands exist | `RfqCommandService` | RFQ status, append-only `SalesTechnicalReview`, audit |
| Quotation lifecycle | `quotationCommands.ts` | create/revision/update/submit/approve/reject/send/accept/decline | quotation command service → `quotation_domain.py` | immutable quotation revisions/lines, approval/customer decisions, audit |
| Convert accepted quote | `orderCommands.ts` | convert-to-order command | `convert_accepted_quotation` | one order per accepted quote, immutable line snapshots, idempotency, audit |
| Progress lifecycle | `orderCommands.ts` | progress/hold/resume/complete/cancel | `transition_order` | order state, append-only progress event and audit event |
| Audit | `orderCommands.ts` | entity timeline and global audit GETs | canonical read service | filtered/paginated `AuditEvent` evidence |

All canonical commands require both exact action and view permissions. Canonical views also reject inactive users, inactive roles, wildcard-only grants, and legacy records (`canonical_permissions.py:59-126`; `canonical_command_service.py:102-168`).

## 6. Feature completion matrix

| Capability | Backend | React screen/action | State | Proven remaining work |
|---|---|---|---|---|
| Customer master | Canonical read/create/update/archive complete | Selector only; admin/customer pages use hard-coded rows | Partial | Build canonical Admin/Sales master screen and errors/empty/loading states |
| Part master | Canonical read/create/update/archive complete | Selector only; product screens use hard-coded rows | Partial | Build Admin-only canonical management screen |
| Material master | Canonical read/create/update/archive complete | Selector only | Partial | Build Admin-only canonical management screen |
| RFQ draft/header/lines/submit | Complete | Implemented | Substantially complete | Browser-integrate and UAT; add archive/resubmit where required by supported lifecycle |
| RFQ document/version/download | Complete | Absent | Missing UI | Add only if needed to complete drawing-required technical review, which current backend requires |
| RFQ Manager review/reject/info | Complete | Absent | Missing UI | Required to reach `READY_TO_QUOTE` through the UI |
| Quotation create/revise/submit | Complete | Implemented | Substantially complete | Browser UAT with ownership and ambiguous outcomes |
| Quotation approve/reject | Complete | Implemented for Manager | Substantially complete | Browser maker-checker UAT with separate accounts |
| Send/customer decision | Complete | Implemented | Substantially complete | Owner confirms who is authorized to record external customer evidence |
| Accepted conversion | Complete | Implemented | Substantially complete | PostgreSQL/browser E2E and idempotent retry proof |
| Order immutable detail/lines | Complete | Implemented | Substantially complete | Browser UAT and legacy write containment |
| Progress/hold/resume/complete/cancel | Complete | Implemented for Admin/Manager | Substantially complete | PostgreSQL/browser concurrency and ambiguous-result UAT |
| Entity timeline/global audit | Complete | Implemented for order/global views | Partial | Confirm timelines needed for RFQ/quotation screens; browser/a11y proof |
| Public/admin/sales dashboard/CRM/news | Multiple noncanonical/prototype surfaces | Mostly hard-coded | Outside canonical MVP unless Owner includes them | Label or remove from internal MVP navigation; do not silently claim production data |

## 7. End-to-end business workflow and missing UAT

| Step | Role | Current frontend action | Endpoint → domain operation | Success/database evidence | Denial/conflict behavior | Automated evidence | Missing UAT/integration |
|---|---|---|---|---|---|---|---|
| Customer create | Admin/Sales | None canonical | `POST customers/commands/create/` → master service | MVP customer + audit | 401/403/400/409; duplicate and legacy denial | Phase 4B API tests | Canonical form, validation, role denial |
| Part/material create | Admin | None canonical | respective create commands | MVP row + audit | Sales/Manager denied | Phase 4B | Admin screen and denial UAT |
| RFQ draft | Admin/Sales | Create RFQ | `POST rfqs/commands/create/` → `RfqCommandService.create` | DRAFT RFQ, number, idempotency, audit | ownership/validation/idempotency conflict | Phase 4B + Phase 5C unit/contract | Browser + real Django/PostgreSQL |
| RFQ lines | owning Admin/Sales | Add/update/remove | RFQ line commands | ordered line rows + audit | non-DRAFT/foreign owner/invalid selector denied | Phase 4B + 5C | Browser validation and stale/offline behavior |
| RFQ submit | owner | Submit | `POST rfqs/{id}/commands/submit/` | `SUBMITTED`, audit | empty/incomplete/non-DRAFT conflict | Phase 4B + 5C | Browser success and denial |
| RFQ review | Manager | None | review start/info/complete/decline | technical-review evidence; `READY_TO_QUOTE` or terminal/intermediate state | only Manager exact grant; evidence requirements | Phase 4B | Entire Manager review UI and UAT; document path where drawing required |
| Quotation create | owning Admin/Sales | Create R0 | RFQ quotation create command | DRAFT R0 with immutable source line snapshots | RFQ not ready/owner/idempotency conflict | Phase 4C + 5D | Full-chain browser run |
| Quotation submit | owner | Submit | quotation submit command | `PENDING_APPROVAL`, immutable commercial data, audit | wrong state/owner denied | Phase 4C + 5D | Browser maker-checker handoff |
| Approval/rejection | Manager | Approve/reject | quotation decision commands | append-only approval + status + audit | maker-checker/role/state denial | Phase 4C + 5D | Separate-account UAT; rejection-revision loop |
| Send/accept/decline | owner Admin/Sales | Record send and customer result | send/customer-decision commands | append-only external evidence + audit | wrong state/owner/missing evidence | Phase 4C + 5D | Owner validates evidence wording and operator responsibility |
| Convert accepted quote | owner Admin/Sales | Convert | convert command → `convert_accepted_quotation` | exactly one order; immutable snapshot lines; audit | only ACCEPTED, once, owner, idempotency conflict | Phase 3D/4C + 5E | PostgreSQL/browser retry UAT |
| Order detail | Admin/Sales/Manager read | Select order | order/detail/lines/progress/timeline GETs | authoritative snapshots/events | exact view required | Phase 4A + 5E | Browser content/responsive checks |
| Progress/hold/resume/complete/cancel | Admin/Manager | Implemented buttons/forms | order commands → `transition_order` | state + exactly one progress/audit event | Sales denied; invalid/duplicate/conflicting state fails atomically | Phase 3D/4D + 5E | PostgreSQL browser UAT and two-actor conflict exercise |
| Global audit | Admin/Manager | Load/paginate | `GET audit-events/` | paginated sanitized audit evidence | Sales/anonymous denied | Phase 4A/4D + 5E | Browser pagination, denial and redaction review |

## 8. Authentication decision status

Current mechanism:

- Email/password login returns an opaque token (`foundation.py:66-88`). The server stores only a SHA-256 token hash and enforces an eight-hour default TTL and active-token limit (`foundation/services.py:117-169`; `base.py:308-312`). Logout revokes the server row; rotation exists server-side (`services.py:192-222`).
- React holds the raw token only in an `InMemoryAuthSession`; it is not placed in local/session storage (`canonical.ts:43-61`). Each canonical request sets `Authorization: Bearer ...` (`canonical.ts:265-275`). Refresh loses the session.
- The UI records `expires_at` but has no timer, proactive expiration, session restore, or token-rotation call (`App.tsx:1555-1614`). Logout clears locally before a fire-and-forget server logout, so network failure may leave the token valid until expiry.
- Role is server-assigned through the user's single `FoundationRole` FK. There is no role selector or active-role switch. The React UI trusts the returned role only for affordances; the backend remains authoritative.
- Canonical routes enforce active user and active canonical role. Older foundation/module permissions check user activity but do not check `FoundationRole.is_active` (`foundation/services.py:42-56`), so inactive-role behavior is not uniform outside canonical routes.
- A 2FA challenge model/service exists, but login does not invoke it and no delivery adapter is integrated (`foundation/models.py:92-103,153-175`; `foundation/services.py:248-286`).
- Request logging records method, resolver route, status, duration, and correlation ID, not bodies or headers (`common/middleware.py:21-83`). Production JSON formatting restricts extra fields (`common/logging.py:9-36`).

Resolved portfolio-demo authentication strategy:

1. Retain the current memory-only opaque Bearer token for the canonical React API. Do not add local storage, session storage, or JavaScript-readable persistent cookies. Serve React and `/api` from one HTTPS origin in the production-like candidate.
2. Keep the server-authoritative configurable absolute TTL (current default eight hours), add client-side expiry handling, do not silently refresh, and make logout visibly confirm server revocation or report a bounded failure before discarding the UI session.
3. Keep one fixed active role per fictional demo account: exactly Admin, Sales, and Manager. Do not add role switching.
4. Do not claim 2FA in Phase 6; the dormant challenge model is not a usable control without a delivery adapter. 2FA is a documented future enhancement, not a blocker for a local portfolio demo.
5. The owning Admin/Sales user may record customer acceptance/decline evidence, matching the current canonical permission/domain contract. All demo identities and evidence are fictional.
6. Django session and CSRF cookies used by Django-rendered/admin surfaces remain `Secure`, `HttpOnly` where supported, and `SameSite=Lax` in production settings. Canonical Bearer commands do not use cookie authentication; CSRF middleware/trusted origins remain configured and are tested for cookie-backed Django surfaces. Production CORS is empty/same-origin by default; explicit cross-origin development origins are narrow and environment-based.

## 9. Role and permission matrix

| Capability | Admin | Sales | Manager | Extra rule |
|---|---:|---:|---:|---|
| View customer/part/material/RFQ/quotation/order | Yes | Yes | Yes | active user, active role, exact view grant |
| Create/change/archive customer | Yes | Yes | No | canonical record only |
| Manage/archive part/material | Yes | No | No | canonical record only |
| Create/change/submit/archive RFQ | Yes | Yes | No | owner/assignee where enforced |
| Technical review RFQ | No | No | Yes | append-only review evidence |
| Create/revise/change/submit/archive quotation | Yes | Yes | No | quotation/RFQ ownership |
| Approve/reject quotation | No | No | Yes | maker-checker boundary |
| Send/record customer decision/convert | Yes | Yes | No | owner; required evidence/state |
| Progress/hold/resume/complete/cancel order | Yes | No | Yes | valid state/percentage/reason |
| View entity timeline | By entity view | By entity view | By entity view | exact entity permission |
| View global audit | Yes | No | Yes | exact `audit:view` |

Frontend affordances for quotation and order reflect this matrix, but RFQ review and canonical master management are missing. Authorization acceptance must be based on backend responses, not hidden buttons.

## 10. Database and migration readiness

| Item | Evidence/status | Phase 6 requirement |
|---|---|---|
| Development DB | SQLite fallback when `DATABASE_URL` is empty (`base.py:56-92,165-167`) | Acceptable for quick local unit work, not authoritative concurrency/UAT |
| Test DB | In-memory SQLite (`test.py:16-21`) | Default CI lane only |
| Production DB | Production requires a PostgreSQL URL and rejects other schemes (`production.py:40-49`) | Use PostgreSQL for Phase 6 integrated/UAT/staging |
| Migrations | Canonical chains end at business core `0005`, sales `0005`, transaction domain `0005`, foundation `0010`; data-classification migrations fail closed on constraint ambiguity | Run `migrate --check`, clean install, upgrade-from-approved snapshot, and forward-only rollback drill on an isolated Phase 6 DB |
| Historical PostgreSQL proof | Phase 3B–4D reports show PostgreSQL 16 migrations, focused suites, concurrency, and full regression passed | Valuable baseline, but rerun current HEAD in Phase 6 environment |
| SQLite operational use | README permits local SQLite; production settings prohibit it | Owner UAT should use PostgreSQL to match concurrency/constraints |
| Seed/demo data | Existing generator creates legacy/demo CRM, quotations/orders and demo roles, not the Phase 3–5 canonical workflow (`demo_data.py:108-189,207-269,450-557`) | Add a safe, fictional, idempotent canonical UAT fixture or scripted API setup; never use real credentials |
| Rollback | Phase 3D reports and migrations require forward correction once MVP_V1 evidence exists | Release procedure must not reverse evidence-bearing migrations automatically |
| Backup/restore | Scripts and isolated restore runbook exist | Execute an isolated PostgreSQL + media restore drill against the chosen Phase 6 topology before release |

Required variable names (values were not read): `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`, `DATABASE_SSLMODE`, `REDIS_URL`, `METRICS_BEARER_TOKEN`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`, `STATIC_ROOT`, `MEDIA_ROOT`, `AUTH_PASSWORD_MIN_LENGTH`, `AUTH_LOGIN_MAX_FAILURES`, `AUTH_LOGIN_WINDOW_SECONDS`, `AUTH_TOKEN_TTL_HOURS`, `AUTH_MAX_ACTIVE_TOKENS`, and frontend `VITE_API_BASE_URL`/namespace overrides. Compose derives database/Redis URLs from its own named variables; no value should enter Git or reports.

## 11. Automated test coverage matrix

Counts are static test-function/call inventory at current HEAD; no tests were run during this discovery.

| Area | Current evidence | Environment | Gap |
|---|---|---|---|
| Phase 3 master/RFQ models + migrations | 25 focused test functions | SQLite default; historical PostgreSQL | Current-HEAD PostgreSQL rerun in Phase 6 |
| Phase 3 quotation models + migrations | 18 | SQLite + historical PostgreSQL/concurrency | Integrated fixture chain |
| Phase 3 order/progress/audit + migrations | 15 | SQLite + historical PostgreSQL/concurrency | Browser-to-DB evidence |
| Phase 4 canonical read | 14 test functions (parameterization expands cases) | Django test DB | Full HTTP browser path absent |
| Phase 4 master/RFQ commands | 18 | SQLite; PostgreSQL-only concurrency included | CI does not run PostgreSQL lane |
| Phase 4 quotation/conversion | 18 | SQLite; 3 PostgreSQL concurrency tests | CI does not run PostgreSQL lane |
| Phase 4 order progress | 15 | SQLite; 4 PostgreSQL concurrency tests | CI does not run PostgreSQL lane |
| Frontend Phase 5 | 120 Node tests: 12 + 18 + 30 + 22 + 38 | No services; intercepted fetch/source-boundary tests | No DOM/component/browser rendering |
| Typecheck/build/format | Scripts exist; Phase 5 reports show passes | No services | Main CI runs only frontend build, not tests/typecheck/format |
| Browser E2E | No Playwright/Cypress config; an older unrelated Python browser smoke exists under `tests/e2e` | Browser/service dependent | No canonical Phase 3–5 E2E |
| Accessibility | No automated axe/pa11y lane | Browser | Missing |
| Responsive layout | Tailwind responsive classes exist | Browser | No viewport assertions/manual matrix |
| Security | Backend hardening tests and source boundaries exist | Mostly no external services | No automated secret scanner, dependency audit gate, browser CSP/CORS auth test |

## 12. Missing integration/UAT matrix

| Gap | Impact | Smallest closing evidence |
|---|---|---|
| Vite has no `/api` proxy and defaults to relative API URLs on port 8443 | Default `pnpm dev` sends API calls to Vite, not Django | Explicit isolated dev routing plus contract test and real browser smoke |
| Root `.env.example` is not a Vite-local env template | Documented `VITE_API_BASE_URL` may not be loaded by Vite from its project directory | Frontend env example/runbook or proxy-based same-origin contract |
| React assets absent from Docker image/Compose/Nginx | Production candidate cannot serve the canonical UI | Selected same-origin static/proxy topology, built and smoke-tested |
| Canonical customer/part/material screens absent | Full workflow cannot begin in React | Role-appropriate master-data UI or a clearly approved UAT fixture boundary |
| RFQ technical review/documents absent | UI cannot progress submitted RFQ to `READY_TO_QUOTE` | Manager review UI plus required document evidence flow |
| Hard-coded public/admin/CRM/dashboard content remains | Internal MVP can misrepresent prototype data as live data | Hide/label outside MVP or integrate only Owner-approved scope |
| Writable legacy endpoints coexist | Alternate routes can update Django-owned rows without canonical exact grants/audit; MVP rows are queryable by legacy services | Deny legacy writes to MVP_V1 and regression-test every colliding route; optionally retire routes after dependency proof |
| No browser/component suite | Loading, empty, conflict, timeout, offline, focus and layout are unproven in a real DOM | Browser E2E framework against isolated Django/PostgreSQL; Playwright is the default unless implementation evidence blocks it |
| No automatic expiry/session recovery | Confusing UX and uncertain production session posture | Implement only after Owner auth decision; test refresh/expiry/logout |
| No current-HEAD integrated PostgreSQL run | Historical unit/API proof is not a Phase 6 release candidate | Fresh isolated migration + E2E + concurrency run |

## 13. Smallest complete UAT matrix

| Scenario | Admin | Sales | Manager | Required result |
|---|---:|---:|---:|---|
| Login/logout/expired or disabled session | Execute | Execute | Execute | no token persistence; denial is clear; revoked/expired credentials stop access |
| Customer create/update/archive | Execute | Execute own permitted flow | Verify denied | canonical audit evidence |
| Part/material create/update/archive | Execute | Verify denied | Verify denied | selector reflects canonical change |
| RFQ draft, edit lines, submit | Execute one | Execute owned primary case | Verify write denied | `SUBMITTED`, immutable/denial behavior correct |
| RFQ review: start → info → resubmit → complete | Observe/closure where allowed | Respond/resubmit owned RFQ | Execute | reaches `READY_TO_QUOTE` with review/document evidence |
| RFQ decline/closure | Admin acknowledgment case | Verify owner visibility | Execute decline | closed/declined audit chain correct |
| Quotation R0 → submit | Execute or Sales observes | Execute owned case | Verify authoring denied | `PENDING_APPROVAL` |
| Reject → revision → resubmit | Observe | Execute revision | Reject then later review | old revision superseded; history retained |
| Approve → send → customer accept | Observe/send if owner | Execute send/decision as owner | Approve | append-only decisions and accepted state |
| Convert → inspect immutable order | Execute or observe | Execute owned conversion | Observe | exactly one order and immutable line snapshots |
| Progress/hold/resume/complete | Execute one path | Verify denied | Execute primary path | state/progress/audit agree |
| Cancel alternative order | Execute or observe | Verify denied | Execute | reason required; terminal state immutable |
| Entity/global audit | Execute | entity-only; global denied | Execute | pagination, redaction, role denial |
| Loading/empty/400/401/403/404/409/timeout/offline | Representative per workspace | Representative | Representative | deterministic recovery, no mock fallback or duplicate mutation |
| Keyboard, screen reader landmarks, zoom, mobile/tablet/desktop | Representative | Full primary workflow | Maker-checker steps | no focus trap, inaccessible labels, overflow, or hidden error |

Service classification: static/source and frontend Node tests require no service; Django unit/API tests require Django's isolated test database; authoritative concurrency and UAT require PostgreSQL; image/topology tests may require Docker only in Phase 6D; browser tests require frontend+Django+PostgreSQL; final wording/usability, auth policy, and acceptance require Owner interaction.

## 14. Environment and service dependency matrix

| Environment | Django | React | DB | Redis | Docker | Browser | Owner |
|---|---|---|---|---|---|---|---|
| Static/unit lane | no running service | Node only | in-memory SQLite for Django tests | no | no | no | no |
| Phase 6A local integration | localhost/container | Vite process | isolated PostgreSQL mandatory for integration acceptance; SQLite only for unit regression | required only for production-settings smoke | justified for isolated DB/runtime | smoke | no |
| Phase 6B canonical E2E | running | running | isolated PostgreSQL mandatory | as required by selected settings | optional | automated | no |
| Phase 6C UAT | running | running | isolated persistent UAT PostgreSQL | configured | optional | automated + manual | yes |
| Phase 6D staging/release | Gunicorn image | same-origin static/proxy build | PostgreSQL | mandatory under production settings | required isolated topology | smoke | operator review |
| Phase 6E acceptance | approved candidate | approved candidate | restored/backup-protected UAT/staging DB | configured | topology dependent | full manual matrix | mandatory |

No Phase 6 task may depend on AI FACTORY, unrelated n8n/Zalo/9Router/Codex Bridge resources, or their credentials.

## 15. Port and Docker resource isolation matrix

| Resource | Repository evidence | Phase 6 rule |
|---|---|---|
| Django host port | 8000 (`README.md:60-66`; Compose `WEB_PORT` default at `docker-compose.yml:12-13`) | Preflight ownership. If occupied, fail closed or use an explicitly selected alternate and update only Phase 6 local config; never stop the owner |
| Vite host port | 8443, strict (`vite.config.ts:32-41`) | Preflight ownership. If occupied, fail closed or Owner selects alternate; keep API origin synchronized |
| PostgreSQL container port | internal 5432; current main Compose does not publish it | Use internal-only networking or an Owner-approved unused loopback port for test tooling |
| Redis | internal 6379; not published | Keep internal-only |
| Existing Compose network/volumes | generated names around `mecprecision-local`, `media-data`, `postgres-data`, `redis-data`, plus unrelated n8n coupling | Do not use the base Compose for Phase 6 integration. Use an explicit project name such as `django-web-t-123-phase6` and Phase 6-only services/resources |
| Web image | `mecprecision-vietnam:prod-local` | Tag Phase 6 candidates uniquely; never overwrite or remove unrelated images |
| Unrelated services | not inspected by this task | No listing, stopping, restarting, attachment, credential access, or shared volume/network use |

At implementation time, port/resource preflight must be configuration/ownership aware. Discovery intentionally did not inspect live processes or Docker.

## 16. Security gap matrix

| Gap | Evidence | Release rule |
|---|---|---|
| Production auth/session hardening incomplete | memory Bearer is implemented; expiry/logout UX is incomplete | Retain memory-only Bearer on one HTTPS origin; add expiry and bounded confirmed logout; keep Django cookies Secure/HttpOnly/SameSite and CSRF-tested |
| Inactive-role inconsistency on legacy module routes | canonical checks role activity; generic foundation permission service does not | Contain legacy routes and add disabled-role regression tests |
| Legacy writes can bypass canonical audit/action grants for shared models | old routes call broad services over unfiltered model querysets | Deny MVP_V1 mutation outside canonical command service before UAT |
| No automated secret scanner | security policy explicitly marks it pending (`SECRETS_MANAGEMENT_POLICY.md:29-37,76-84`) | Add CI scanner and keep findings sanitized |
| Cross-origin dev is manual | CORS list is configurable; no Vite proxy; frontend sends Bearer, not cookies | Test exact allowed/disallowed origins; prefer same-origin for production |
| CSRF policy depends on auth choice | middleware exists; current Bearer API does not use browser cookies | Document/test explicit rule after Owner auth decision |
| Logout revocation is not awaited by UI | `App.tsx:1603-1614` | Define fail-closed UX and revocation verification |
| 2FA dormant | model/service exists but login does not invoke it | Owner decides requirement; do not advertise as active |
| Media/RFQ documents | backend validates bounded uploads, but production storage is local volume | malware scanner, retention, backup and download authorization must pass staging drill |
| Frontend dependency/security gate absent | CI build only | Add lockfile audit policy without uncontrolled upgrades |

## 17. Production-readiness checklist

| Control | Current | Exit condition |
|---|---|---|
| Split dev/staging/prod settings | Present | configuration validation tests pass |
| `DEBUG=False`, hosts, HTTPS, secure cookies/HSTS | Present in production settings | proxy-aware staging smoke passes |
| CORS/CSRF | Configurable, not end-to-end proven | chosen topology and auth policy tested |
| Secret injection | env fail-closed; secret manager only documented as future | real secret store selected and masked-log verification passes |
| React static delivery | Missing | approved build served with SPA fallback and API same-origin/correct CORS |
| Django static/media | WhiteNoise + local media volume | collectstatic/media upload/download/backup smoke passes |
| Docker images/Compose | Django image exists; base Compose couples unrelated service and omits React | isolated Phase 6 topology builds and has unique resources |
| Liveness/readiness | public health + protected dependency health exist | probes separate liveness from required readiness and avoid unrelated optional dependencies |
| Logging/redaction | structured production logging and safe fields exist | staging review proves no credentials/PII/body leakage |
| Audit logging | canonical `AuditEvent` exists | full UAT event chain reconciles with UI/database evidence |
| Backup/restore | scripts/runbooks exist | isolated restore drill on release topology passes |
| Migration execution | migrations and checks exist | clean/upgrade/rollback-or-forward-fix procedure passes |
| Monitoring/alerting | Prometheus/Grafana artifacts exist | Phase 6 staging alert routing and ownership verified |
| CI | backend SQLite + frontend build | add frontend tests/typecheck/format, PostgreSQL canonical lane, E2E, security gates |
| CD | absent (`README.md:157-164`) | Owner-approved manual or automated promotion with approvals |
| Rollback | runbook/simulations exist | candidate image rollback plus DB forward-fix rule rehearsed |
| Release tag/manifest | no Phase 6 policy | signed-off commit, immutable image digest, changelog and tag naming approved |
| Owner/operator docs | partial/stale | one current start/UAT/deploy/backup/restore/rollback handbook |

Documentation drift is itself a gap: `README.md:107-108` says the frontend has no test script, while current `package.json:11-18` defines tests and typechecks.

## 18. Proposed Phase 6 roadmap

### Phase 6A — isolated production-like full-stack foundation and write-boundary closure

1. **Objective:** make React/Vite reach Django predictably with an isolated PostgreSQL runtime, production-like environment validation, deterministic startup, bounded waits, and no noncanonical mutation of MVP_V1 records.
2. **Authoritative inputs:** Owner scope above; Vite/API settings; Django split settings; URL maps; canonical permissions; legacy route/service inventory; Phase 4D write-boundary rules; current Dockerfile/Compose evidence.
3. **Boundary:** development routing/env templates, Phase 6-only PostgreSQL/web runtime definition, collision preflight, bounded health waits, legacy MVP_V1 write denial, focused transport/configuration/permission tests, and local runbook. No new business workflow screen.
4. **Likely paths:** `figma_make_frontend/vite.config.ts`, a frontend env example, a Phase 6-specific Compose file, Docker/startup helpers, `README.md`/`docs/phase6/`, selected legacy services/views or a centralized guard, backend/frontend tests, `.github/workflows/ci.yml`.
5. **Prohibited:** canonical domain semantics/migrations unless a proven defect requires a separately approved change; real data/credentials; AI/OCR/chatbot/forecasting/n8n/Zalo/AI FACTORY/external automation/payments; unrelated services; the base Compose n8n service.
6. **Services:** static/unit lane none; integration lane uses Vite, Django, and an isolated PostgreSQL 16 resource. Redis is included only for production-settings validation where current settings require it. Docker is justified for disposable PostgreSQL/resource isolation, not for unrelated services.
7. **Isolation:** default evidence ports 8000/8443; preflight and fail closed on collision; explicit Compose project `django-web-t-123-phase6`; Phase 6-prefixed containers/networks/volumes; loopback-only published ports; no stopping or enumerating unrelated resources.
8. **Acceptance:** one documented bounded command sequence creates only Phase 6 resources, migrates PostgreSQL, starts both apps, passes health/readiness, and permits browser login plus canonical RFQ GET; every colliding legacy write rejects MVP_V1; configuration contains no credential; teardown targets only verified Phase 6 resources.
9. **Automated tests:** URL resolution, allowed/disallowed origins, production settings validation, migration check on PostgreSQL, legacy-write matrix, inactive role, frontend tests/typecheck/build/format, backend focused/full SQLite plus focused PostgreSQL smoke.
10. **Owner checks:** optional visual connection smoke; no workflow acceptance yet.
11. **Reports:** implementation task creates `PHASE_6A_FULL_STACK_FOUNDATION_IMPLEMENTATION_REPORT.md`; independent review creates `PHASE_6A_INDEPENDENT_REVIEW_REPORT.md`; checkpoint creates `PHASE_6A_CHECKPOINT_REPORT.md`; any gate failure creates `PHASE_6A_BLOCKED_REPORT.md`.
12. **Checkpoint:** commit only exact intended paths after independent review, clean test evidence, and verified task-owned resource cleanup.
13. **Dependency:** baseline HEAD in this report.
14. **Rollback/fail closed:** revert Phase 6A commit; routing/configuration errors and occupied ports block start; never fall back to legacy/mock data.

### Phase 6B — complete canonical workflow UI and PostgreSQL browser E2E

1. **Objective:** complete only the missing canonical master-data, RFQ document/review/resubmit/closure UI needed for the stated workflow, then automate browser-to-database happy and denial paths.
2. **Inputs:** Phase 6A checkpoint; canonical URLs/serializers/services/models; Phase 3–5 tests.
3. **Boundary:** Admin/Sales Customer management, Admin Product/Part management, supporting Material selectors, Manager RFQ review, required RFQ documents, workflow orchestration, browser E2E, and fictional canonical demo fixtures. Product in the Owner flow maps to the backend's canonical Part (`BusinessProduct`) contract; Phase 6 must use one consistent user-facing term without changing domain meaning.
4. **Likely paths:** new `src/components/*Workspace.tsx`, typed API clients/tests, `App.tsx`, browser-test config/tests, safe fixture command, CI PostgreSQL service lane, docs.
5. **Prohibited:** unrelated public/CRM/AI/OCR/chatbot/forecasting screens, real customer data, n8n/Zalo/AI FACTORY/external automation/payments, production deployment.
6. **Services:** Django, Vite/served build, isolated PostgreSQL; Redis only if chosen settings require it.
7. **Isolation:** unique DB name/user/schema/resources; loopback-only published ports; teardown only resources created by the task.
8. **Acceptance:** a real browser completes Customer/Product → RFQ → quotation → approval/acceptance → order → progress → entity timeline → global audit against PostgreSQL; rejection/revision and information/resubmit alternatives pass; DB evidence reconciles; all role denials pass; no mock or legacy fallback appears.
9. **Tests:** frontend 120 baseline plus new component/E2E; backend full SQLite and current-HEAD PostgreSQL; migration and concurrency lanes.
10. **Owner checks:** review fictional workflow labels/evidence fields; no credentials in repo.
11. **Reports:** `PHASE_6B_CANONICAL_WORKFLOW_IMPLEMENTATION_REPORT.md`, `PHASE_6B_INDEPENDENT_REVIEW_REPORT.md`, `PHASE_6B_CHECKPOINT_REPORT.md`, or `PHASE_6B_BLOCKED_REPORT.md` as applicable.
12. **Checkpoint:** independent review plus repeatable clean environment run.
13. **Dependency:** 6A.
14. **Rollback/fail closed:** delete only task-owned fixture DB/resources; never reverse evidence-bearing migrations; ambiguous commands remain ambiguous until authoritative reconciliation.

### Phase 6C — role-based Owner UAT, accessibility, and session validation

1. **Objective:** give the Owner a stable UAT environment and close browser usability/accessibility/session gaps.
2. **Inputs:** 6B candidate and the resolved portfolio security/session policy in section 20.
3. **Boundary:** memory-only Bearer session expiry/logout UX, fixed-role demo accounts, browser state/error matrix, accessibility/responsive fixes, and exact UAT scripts/results.
4. **Likely paths:** auth client/session components, a11y/UI files, browser tests, UAT handbook/results template.
5. **Prohibited:** expanding product scope based on prototype screens; real production accounts/data; every Owner-declared out-of-scope capability.
6. **Services:** full isolated UAT stack and supported browsers.
7. **Isolation:** dedicated UAT origin/database/storage; no cross-project credentials or ports.
8. **Acceptance:** the section 13 Admin/Sales/Manager matrix passes; loading, empty, timeout, offline, forbidden, conflict, not-found, and server-error states are browser-proven; zero critical/high accessibility/security defects; session expiry and confirmed logout behave as specified.
9. **Tests:** browser keyboard/viewport/accessibility, 401/403/409/timeout/offline, logout/expiry, multi-user maker-checker.
10. **Owner checks:** mandatory Admin/Sales/Manager sign-off and wording/usability decisions.
11. **Reports:** `PHASE_6C_UAT_IMPLEMENTATION_REPORT.md`, `PHASE_6C_INDEPENDENT_REVIEW_REPORT.md`, `PHASE_6C_OWNER_UAT_RESULT.md`, `PHASE_6C_CHECKPOINT_REPORT.md`, or `PHASE_6C_BLOCKED_REPORT.md` as applicable.
12. **Checkpoint:** no checkpoint verdict until signed result and all blocking defects closed.
13. **Dependency:** 6B.
14. **Rollback/fail closed:** revoke UAT tokens, preserve evidence, revert candidate; no production promotion on failed/unsigned UAT.

### Phase 6D — isolated staging, operations, and release readiness

1. **Objective:** produce a safely deployable, observable, recoverable portfolio-demo candidate with one public same-origin entrypoint.
2. **Inputs:** 6C checkpoint/sign-off, resolved topology/security policy, production settings, Docker/static/ops artifacts.
3. **Boundary:** production React build served by a static web/reverse proxy on the same HTTPS origin, `/api` and media proxying to Django, isolated web/Django/PostgreSQL/Redis resources, readiness, migration job, CI gates, backup/restore, monitoring, rollback, and operator docs. Django remains the sole application backend.
4. **Likely paths:** `Dockerfile`, a Phase 6-specific Compose/deployment file, frontend build config, Nginx/platform config, `.github/workflows/`, `ops/`, `scripts/`, `docs/runbooks/`; base unrelated service definitions remain untouched unless separately authorized.
5. **Prohibited:** public production deployment without Phase 6E authorization, shared volumes/networks, unrelated service control, real secret material in Git/evidence, destructive migration rollback, all Owner-declared out-of-scope capabilities.
6. **Services:** isolated staging PostgreSQL/Redis/web/frontend/proxy; no unrelated n8n/AI dependencies for canonical MVP readiness.
7. **Isolation:** explicit project/resource prefix, immutable image tag/digest, no default-name collision, no broad cleanup.
8. **Acceptance:** deterministic bounded startup, clean deploy/upgrade, `DEBUG=False`, allowed-host/origin/cookie settings, frontend SPA/static/media delivery, liveness/readiness, sensitive-data-safe logging, backup/restore, CI, alert and rollback drills pass.
9. **Tests:** production settings check, image non-root/static smoke, PostgreSQL migrations/concurrency/E2E, dependency/security scanning, restore and rollback drills.
10. **Owner checks:** staging URL, hosting, retention/monitoring owners, release window.
11. **Reports:** `PHASE_6D_STAGING_IMPLEMENTATION_REPORT.md`, `PHASE_6D_OPERATIONS_REVIEW_REPORT.md`, `PHASE_6D_RELEASE_CANDIDATE_CHECKPOINT_REPORT.md`, or `PHASE_6D_BLOCKED_REPORT.md` as applicable.
12. **Checkpoint:** immutable candidate manifest only after independent operational review.
13. **Dependency:** 6C.
14. **Rollback/fail closed:** preserve DB/media; roll application image back; use forward corrective migration; failed readiness blocks promotion.

### Phase 6E — final Owner acceptance and release checkpoint

1. **Objective:** reconcile all evidence and authorize or reject the production candidate.
2. **Inputs:** signed 6C UAT, 6D candidate manifest/drills, resolved Phase 6 policy, and open-risk register.
3. **Boundary:** verification/reporting/tag preparation only; deployment requires a separate explicit authorization.
4. **Likely paths:** final acceptance report, release checklist/changelog/manifest.
5. **Prohibited:** code fixes mixed into acceptance, production mutations, implicit tag/push/deploy.
6. **Services:** staging candidate only.
7. **Isolation:** verify exact commit/image/database migration target and no shared-resource collision.
8. **Acceptance:** no unresolved blocking gaps; all matrices trace to the immutable candidate; clean Git release checkpoint; setup/demo/operations documentation is executable; Owner signs `READY_FOR_PORTFOLIO_PRODUCTION_DEMO` or records rejection.
9. **Tests:** rerun release gates from immutable candidate.
10. **Owner checks:** mandatory final workflow, security, recovery and go/no-go acceptance.
11. **Reports:** `PHASE_6E_FINAL_VALIDATION_REPORT.md`, `PHASE_6E_OWNER_ACCEPTANCE_REPORT.md`, `PHASE_6E_RELEASE_CHECKPOINT_REPORT.md`, or `PHASE_6E_BLOCKED_REPORT.md` as applicable.
12. **Checkpoint:** tag/release only in a later explicitly authorized action.
13. **Dependency:** 6D.
14. **Rollback/fail closed:** any mismatch, stale evidence or unsigned decision returns `NOT_APPROVED`; do not tag or deploy.

## 19. Exact first Phase 6 implementation task

**Task:** Phase 6A — create the collision-safe React/Vite + Django + PostgreSQL production-like integration foundation and close the legacy MVP_V1 write boundary.

Exact scope:

1. Add one documented, testable local routing contract: Vite proxies `/api` to a configurable loopback Django origin, while frontend code keeps root-relative canonical URLs. This matches the selected same-origin production topology and existing `connect-src 'self'` policy. Explicit cross-origin development remains narrow, environment-based, and separately tested.
2. Add a Phase 6-specific runtime definition containing only the necessary Django, PostgreSQL 16, and production-settings Redis dependency. Do not include or contact n8n, AI, OCR, chatbot, forecasting, Zalo, AI FACTORY, or external automation. Use an explicit Compose project/resource prefix and no shared volumes/networks.
3. Add deterministic startup/migration/readiness orchestration with bounded waits. A failed migration, unavailable dependency, unhealthy service, or timeout must stop the Phase 6 stack and create a sanitized blocked report.
4. Add a port-preflight gate for 8000/8443 that reports collision and exits without stopping processes. Alternate ports must be explicit and update routing consistently.
5. Inventory every routed legacy write that touches `BusinessCustomer`, `BusinessProduct`, `SalesRfq`, `SalesQuotation`, or `TransactionOrder`. Add a centralized fail-closed guard so `MVP_V1` rows can be mutated only through canonical command/domain paths. Preserve intentionally legacy-only creation/read behavior and the Phase 4D order guard.
6. Add regression tests for unauthenticated, inactive-user, inactive-role, wildcard-only, wrong-role, and legacy-route attempts against MVP_V1 rows; prove no row/audit count changes on denial.
7. Promote frontend test/typecheck/build/format, backend tests, migration consistency, and an isolated PostgreSQL integration smoke into main CI where deterministic.
8. Update the stale root README and add the Phase 6A runbook with exact start/stop commands, env-file locations, bounded waits, ports/resources, cleanup ownership, and current frontend test commands.

Expected paths (final list must be narrower if implementation proves fewer are needed):

- `figma_make_frontend/vite.config.ts`
- `figma_make_frontend/.env.example` or an equally explicit non-secret template
- a Phase 6-specific Compose/runtime file that excludes all out-of-scope services
- a bounded Phase 6 startup/readiness helper
- `django_backend/apps/api/` or owning legacy service modules for the centralized guard
- focused backend boundary test file(s)
- focused frontend routing/config test file
- `.github/workflows/ci.yml`
- `README.md`
- `docs/phase6/` local integration runbook if README would become unwieldy
- `PHASE_6A_FULL_STACK_FOUNDATION_IMPLEMENTATION_REPORT.md`
- a separate Phase 6A independent-review/checkpoint/blocked report for each corresponding task

Acceptance criteria:

- clean static/unit gates pass without services;
- Django, Vite, PostgreSQL, and required production-settings Redis can be started deterministically on verified task-owned ports/resources with bounded waits;
- clean PostgreSQL migrations and `migrate --check` pass at current HEAD;
- real-browser login and canonical RFQ GET reach Django with no HTTP mock;
- exact allowed origin works and an unapproved origin is denied where cross-origin mode is used;
- all legacy colliding writes reject MVP_V1 without mutation or audit fabrication;
- canonical commands retain existing behavior and full Phase 3–5 regressions pass;
- no source uses browser token persistence, logs credentials, or silently falls back to mock data;
- all created Docker resources are explicitly Phase 6-owned; no out-of-scope or unrelated service is inspected, contacted, started, stopped, or modified;
- independent review confirms only intended paths changed and `git status --short` matches the report.

## 20. Owner decision resolution and fixed Phase 6 policy

The Owner's authoritative scope resolves the discovery blocker. Phase 6 proceeds with these fixed planning decisions:

1. **Target:** `READY_FOR_PORTFOLIO_PRODUCTION_DEMO`, not a claim of public commercial production certification.
2. **Architecture:** React production assets and the Django canonical API share one HTTPS origin. A static server/reverse proxy may serve assets and proxy `/api`; Django remains the only application backend. No microservices or worker are added without a proven technical need.
3. **Authentication:** memory-only Bearer tokens, server-enforced expiry, no silent refresh or browser persistence, bounded confirmed logout, and fixed Admin/Sales/Manager demo roles. Secure Django cookies and CSRF settings remain enabled for cookie-backed Django surfaces. 2FA is not claimed.
4. **Data:** PostgreSQL is mandatory for integration, E2E, UAT, staging, migration, backup, and restore evidence. SQLite remains a unit/development fallback only. All seeded identities, customers, products, RFQs, quotations, orders, and evidence are fictional and contain no personal or secret data.
5. **MVP navigation:** the canonical workflow is the demonstrable portfolio product. Noncanonical hard-coded public/admin/CRM/dashboard screens must be clearly marked demo-only or removed from the Phase 6 demo navigation; they are not silently expanded or represented as live canonical data.
6. **Customer decisions:** the owning Admin/Sales operator records fictional external acceptance/decline evidence, as the current canonical contract requires.
7. **Isolation:** Phase 6 uses explicit project/resource names and preflighted ports. It never displaces, inspects, or shares resources with unrelated projects.
8. **Secrets/operations:** values are injected at runtime from ignored local environment storage for the portfolio demo; none are committed or printed. CI uses secret storage. Monitoring recipients, backup retention, public hosting, and real production deployment remain environment/operator choices and do not block a local production-like portfolio verdict when documented as such.
9. **Reporting:** every implementation, independent review, checkpoint, or blocked task in Phase 6A–6E creates its own Markdown report. No report may combine an implementation and its nominally independent review.

## 21. Safety confirmation and final Git state

This discovery made no implementation change. It did not stage, commit, push, merge, rebase, tag, deploy, change branches, start/restart a process, make an HTTP request, start Docker/PostgreSQL/a database, inspect live ports/processes/containers, submit a form, or access external-service credentials. It did not read credential values. The only filesystem change is this mandatory report.

Final expected `git status --short` after report creation:

```text
?? PHASE_6_SCOPE_DISCOVERY_AND_RELEASE_PLAN.md
```

The report SHA-256 is intentionally not embedded here; it is supplied only in terminal output.
