# Phase 5B Foundation Login and RFQ Read Integration Report

## Final verdict

`READY_FOR_PHASE_5B_CHECKPOINT_AFTER_REVIEW_REPAIR`

Phase 5B implements the first consumer of the Phase 5A frontend foundation:
Foundation login/logout with in-memory token handoff, plus exactly one
read-only canonical RFQ list integration on the existing `sales-quotes` slice.
The independent Phase 5B review then repaired three proven frontend defects:
documented API-root topology support for local Vite development, cancellable
latest-login handling in `App.tsx`, and password clearing on submit.
No backend, database, migration, command endpoint, AI Factory/n8n/Zalo/9Router,
Codex Bridge, port, push, merge, rebase, stash, reset, deployment, or checkpoint
commit was performed.

## Initial repository state

| Item | Verified value |
| --- | --- |
| Git root | `C:/Users/hoang/Documents/ChatGPT/WEB Ô TÔ DJANGO` |
| Remote | `https://github.com/hoangquocquan/Django-web-t-123.git` |
| Branch | `codex/demo-database-validation` |
| Baseline HEAD | `fc244cb3ca2fabfbac432bbe896589e2549cf131` |
| Baseline subject | `phase5a: add canonical frontend transport foundation` |
| Initial status | Clean |

## Proven endpoint and contract evidence

| Contract | Evidence |
| --- | --- |
| Browser topology | `django_backend/config/urls.py:12-13` mounts integrated same-origin `/api/v1/`; `figma_make_frontend/vite.config.ts:32` has the Vite server config and no proxy; `.env.example:13-15` documents Vite origin `http://localhost:8443` and Django API root `http://127.0.0.1:8000`. Phase 5B now resolves `VITE_API_BASE_URL` into exact Foundation and canonical namespaces without adding permissive CORS/proxy behavior. |
| Login route | `django_backend/apps/api/urls.py:203` maps `foundation/auth/login/`; frontend resolves `/api/v1/foundation/auth/login/` or `{VITE_API_BASE_URL}/api/v1/foundation/auth/login/` in `figma_make_frontend/src/api/foundation.ts:184-213,359-379`. |
| Login method/fields | `django_backend/apps/api/views/foundation.py:66-76` proves POST; `django_backend/apps/api/serializers/foundation.py:13-17` proves `email` and `password`. |
| Login success | `django_backend/apps/api/views/foundation.py:82-87` returns canonical success data with `token`, `expires_at`, and `user`; frontend validates this in `foundation.ts:37-100` and stores only the token in `InMemoryAuthSession` at `foundation.ts:239`. |
| Login rejection/error envelope | `foundation.py:79-80` and `canonical_contract.py:50-55` prove sanitized error envelopes; frontend returns generic login rejection text at `foundation.ts:247-255`. |
| Token expiry | `django_backend/apps/foundation/services.py:141-148` creates `token_urlsafe(32)` with `expires_at`; `services.py:183-189` rejects expired tokens. Phase 5B does not implement refresh/rotation. |
| Logout route | `django_backend/apps/api/urls.py:204` maps `foundation/auth/logout/`; `foundation.py:91-101` revokes current Bearer token and returns `logged_out`; frontend clears memory before optional revoke in `App.tsx:1555-1569`. |
| RFQ list route | `django_backend/apps/api/canonical_urls.py:221` maps `rfqs/`; frontend requests only `rfqs/?limit=20&ordering=-created_at` in `figma_make_frontend/src/api/rfq.ts:54,102-106`. |
| RFQ auth/permission | `canonical.py:165-186` binds RFQ list to `rfq:view`; `canonical_permissions.py:11,59-86` requires active user, active role, allowed Admin/Sales/Manager role, and exact non-wildcard permission. |
| RFQ schema | `django_backend/apps/api/serializers/canonical.py:120-143` proves the RFQ JSON fields; frontend validates the aligned page/item shape in `rfq.ts:1-100`. |
| Pagination/filter/ordering | `canonical_contract.py:17-19,119,154-168` proves limit/offset/ordering envelope and unsupported-filter behavior; `canonical.py:169-183` proves RFQ filters and ordering allowlist. |

## App.tsx TypeScript repairs

The five pre-existing parser failures were the inline prop-type declarations
reported around old lines 59, 99, 154, 927, and 1108. Phase 5B repaired them
mechanically by adding valid separators/named types while preserving the visual
component behavior:

- `Badge` now uses `ReactNode` and a separated optional `tone`.
- `Field` now uses a valid props object and optional form-control fields for
  the real login form.
- `DataTable` now uses `DataTableProps`.
- `AdminPage` now uses a valid props object plus auth callbacks.
- `SalesPage` now uses a valid props object plus RFQ read state.

Full frontend TypeScript now passes.

## Authentication lifecycle

`App.tsx:1499-1610` owns the Phase 5B lifecycle. Login submits only email and
password to the proven Foundation endpoint, stores the returned access token
only in the Phase 5A `InMemoryAuthSession`, uses AbortController plus a latest
request guard to reject stale login responses, clears the password field on
submit, and navigates to the admin shell only for the current login request.
Logout captures the current token, aborts pending login/RFQ work, invalidates
stale guards, clears memory immediately, returns to login, and only then calls
the proven logout endpoint for server-side revocation. HTTP 401 during RFQ load
clears the in-memory session and returns the RFQ slice to unauthenticated state;
there is no authenticated retry.

## RFQ read-only data flow

The existing `sales-quotes` slice is the single integrated read-only RFQ
consumer (`App.tsx:1413`). It renders `RfqPanel` (`App.tsx:1277-1319`) and no
longer contains the old mock rows. The RFQ loader (`App.tsx:1549-1581`) uses
the Phase 5A `createCanonicalClient`, the fixed `rfqs/` read path, an
`AbortController`, and a latest-request guard. Logout and authentication changes
also invalidate old RFQ requests. It exposes deterministic states
for unauthenticated, loading, populated, empty, permission denied, timeout,
network, protocol, and server failure.

## Exact changed paths

| Path | Purpose |
| --- | --- |
| `figma_make_frontend/package.json` | Adds full app typecheck, Phase 5A typecheck, and split Phase 5A/5B test scripts. |
| `figma_make_frontend/src/App.tsx` | Repairs five TypeScript declarations and connects Foundation login/logout plus one RFQ read-only slice. |
| `figma_make_frontend/src/api/foundation.ts` | Foundation auth client with bounded login/logout, sanitized errors, namespace-contained URL validation, root-relative integrated mode, and documented `VITE_API_BASE_URL` support for Vite dev. |
| `figma_make_frontend/src/api/rfq.ts` | Canonical RFQ page/item types, schema guard, table-row mapper, error-state mapper, and stale-request guard. |
| `figma_make_frontend/src/api/phase5b.test.ts` | Deterministic Phase 5B tests. |
| `PHASE_5B_FOUNDATION_LOGIN_AND_RFQ_READ_INTEGRATION_REPORT.md` | This report. |

## Test matrix and exact results

| Command | Result |
| --- | --- |
| `pnpm --dir figma_make_frontend run typecheck` | Passed: full `tsconfig.json`. |
| `pnpm --dir figma_make_frontend run typecheck:phase5a` | Passed: strict Phase 5A API gate. |
| `pnpm --dir figma_make_frontend run test:phase5a` | Passed: 12 tests, 0 failed, 244.9762 ms. |
| `pnpm --dir figma_make_frontend run test:phase5b` | Passed: 18 tests, 0 failed, 187.7076 ms. |
| `pnpm --dir figma_make_frontend run test` | Passed: 30 tests, 0 failed, 248.3882 ms. |
| `pnpm --dir figma_make_frontend run format src/App.tsx src/api/foundation.ts src/api/phase5b.test.ts src/api/rfq.ts` | Passed after formatting changed Phase 5B files. |
| `pnpm --dir figma_make_frontend run build` | Passed: Vite 8.0.5, 19 modules transformed, built in 217 ms. |
| `git diff --check` | Passed; only CRLF conversion warnings for tracked frontend files. |
| Lint | No configured lint script exists. |

No browser framework exists in the repository, so no new browser framework was
installed. All login/RFQ tests use deterministic intercepted `fetch` functions
and no live services.

## Security inspection

- No token persistence: no `localStorage`, `sessionStorage`, cookies, or
  IndexedDB in implementation.
- No Authorization or credential logging: no console calls in changed
  implementation.
- No raw backend body or fetch exception leakage: Foundation and canonical
  errors are converted to controlled messages.
- No realistic credential fixture: tests use `.test` email and short
  non-production sentinel strings only.
- No unsafe HTML injection: no `dangerouslySetInnerHTML`, `innerHTML`, or
  adjacent HTML insertion in changed implementation.
- No permissive CORS, CSRF, middleware, endpoint, proxy, or port change.
- Backend permissions remain authoritative; the client maps errors but does
  not reproduce or replace permission enforcement.
- Requests are bounded/cancellable through Phase 5A canonical transport and the
  Phase 5B Foundation bounded fetch helper.
- RFQ requests remain inside the Phase 5A canonical namespace.

## Compatibility evidence

- No backend path changed.
- No migration, lockfile, generated `dist/`, Docker, PostgreSQL, or Django
  state changed.
- General mock modules remain untouched for unrelated screens.
- Only the `sales-quotes` slice stops using inline mock rows after canonical
  RFQ integration starts.
- Existing public navigation and unrelated sales/admin screens remain in the
  same monolithic Figma-derived layout.

## SHA256 manifest

| Path | SHA256 |
| --- | --- |
| `figma_make_frontend/package.json` | `20AAA9EE5F8576C73B78DD4546601E73112F4ABFC838F7A637E852A77E308CDD` |
| `figma_make_frontend/src/App.tsx` | `CD7771768DDE282309BB9332F62D957EC88027886E6EB0AD4AB6D06C8B81C784` |
| `figma_make_frontend/src/api/foundation.ts` | `CBFEBD32BE1856D5D7CCD14107B85F93AE8D8FC6672A0D0BB51F2564F097F62E` |
| `figma_make_frontend/src/api/rfq.ts` | `447932075694C3D28FC1898F88FC9B7AAB065FFCD0FA5B759D53812C46E0ED78` |
| `figma_make_frontend/src/api/phase5b.test.ts` | `D5BE1298173C4073C3EC9C677B305B9A8F9A3055C55325771E80AF51274A6F4E` |

This report's digest is intentionally not embedded in itself.

## Git diff stat and final status

Tracked diff stat after independent repair was:

```text
 figma_make_frontend/package.json |   7 +-
 figma_make_frontend/src/App.tsx  | 418 ++++++++++++++++++++++++++++++++++-----
 2 files changed, 370 insertions(+), 55 deletions(-)
```

Final status is expected to include those tracked changes plus untracked
`foundation.ts`, `rfq.ts`, `phase5b.test.ts`, and this report. No commit was
created.

## Remaining Phase 5 work

Future Phase 5 work should select the next canonical screen explicitly, define
profile/session refresh or rotation behavior if needed, and add real UI flow
tests if a browser test framework is later introduced. Write/command screens
remain out of scope until separately authorized.

## Checkpoint recommendation

Phase 5B is ready for independent review. Do not checkpoint until that review
confirms the changed-path set, validation results, security inspection, and
owner acceptance boundary.
