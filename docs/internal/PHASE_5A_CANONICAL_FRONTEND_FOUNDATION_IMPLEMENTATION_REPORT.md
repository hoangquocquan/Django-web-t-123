# Phase 5A Canonical Frontend Foundation Implementation Report

## Final verdict

`READY_FOR_PHASE_5A_CHECKPOINT`

Phase 5A now implements the authorized React canonical transport and
authentication foundation, including the independent review repairs. It still
does not connect a business screen, acquire a token from a live endpoint, change
backend behavior, duplicate a domain rule, alter a database, contact a live
service, or touch AI Factory/n8n/Zalo/9Router/Codex Bridge surfaces.

## Authoritative Owner designation

The Owner designated the current MVP continuation after commit
`27002cbf830285f261dda91f1e8b39cd6d72ed3b` as **Phase 5 - React Frontend
Integration with the Canonical API**. This designation renumbers the frontend
integration formerly documented as Phase 6 for the current MVP sequence only.
Historical CRM migration, Business UI, and AI Factory meanings of "Phase 5"
remain outside this scope.

The first authorized subphase is **Phase 5A - Canonical Frontend Transport and
Authentication Foundation**. Its acceptance boundary is a tested transport and
in-memory auth boundary, not business-screen conversion.

## Initial repository evidence

| Item | Verified value |
| --- | --- |
| Working directory / Git root | `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO` |
| Repository | `Django-web-t-123` |
| Remote | `https://github.com/hoangquocquan/Django-web-t-123.git` |
| Branch | `codex/demo-database-validation` |
| HEAD | `27002cbf830285f261dda91f1e8b39cd6d72ed3b` |
| Subject | `phase4d: add order progress audit command APIs` |
| Parent | `86e2a0f669acd05764ab05bdf1ec7c64524cab16` |

The Phase 4D checkpoint and the authoritative Phase 5 designation were verified
before implementation and again during independent review.

## Exact changed paths

| Path | Purpose |
| --- | --- |
| `figma_make_frontend/src/api/canonical.ts` | Typed canonical base URL, in-memory auth, bounded transport, strict envelopes, and safe error mapping. |
| `figma_make_frontend/src/api/canonical.test.ts` | Deterministic Node tests for the Phase 5A boundary and review repairs. |
| `figma_make_frontend/tsconfig.phase5a.json` | Isolated strict type-check gate for the new foundation and tests. |
| `figma_make_frontend/package.json` | Adds `test` and Phase 5A `typecheck` scripts; no dependency version changes. |
| `PHASE_5_SCOPE_DISCOVERY_AND_IMPLEMENTATION_PLAN.md` | Records and resolves the Owner decision. |
| `PHASE_5A_CANONICAL_FRONTEND_FOUNDATION_IMPLEMENTATION_REPORT.md` | This implementation report. |
| `PHASE_5A_INDEPENDENT_REVIEW_AND_REPAIR_REPORT.md` | Independent review findings, repairs, and final readiness evidence. |

No lockfile, app screen, mock file, backend file, migration, generated `dist/`
artifact, or legacy endpoint changed.

## Implementation references

- `figma_make_frontend/src/api/canonical.ts:1-3`: default canonical namespace
  and bounded 10-second default / 30-second maximum.
- `figma_make_frontend/src/api/canonical.ts:5-40`: typed success/error contracts
  and sanitized client error.
- `figma_make_frontend/src/api/canonical.ts:43-61`: injectable `AuthSession`
  and private in-memory token lifecycle.
- `figma_make_frontend/src/api/canonical.ts:63-108`: single
  `VITE_CANONICAL_API_BASE_URL` boundary, constrained to exact
  `/api/v1/canonical/` root-relative or HTTP(S) absolute base.
- `figma_make_frontend/src/api/canonical.ts:122-150`: strict envelope guards and
  stable HTTP-status-based classification.
- `figma_make_frontend/src/api/canonical.ts:153-227`: relative path escape
  rejection, encoded traversal/separator rejection, token validation, and
  timeout bounds.
- `figma_make_frontend/src/api/canonical.ts:230-240`: invalid JSON/body parse
  failure becomes a generic protocol error without raw body text.
- `figma_make_frontend/src/api/canonical.ts:243-369`: request orchestration,
  caller-header removal, auth-session Bearer injection, first abort reason,
  timeout race bounding, network redaction, and listener/timer cleanup.

## Authentication and token-lifecycle boundary

`InMemoryAuthSession` stores an opaque value only in a private runtime field.
It provides explicit set, get, and clear operations and rejects blank,
whitespace-wrapped, control-character, newline-bearing, and bearer-invalid
values. It never reads or writes `localStorage`, `sessionStorage`, cookies,
IndexedDB, source files, reports, fixtures, or logs.

Callers cannot supply their own `Authorization` request header: the transport
deletes it case-insensitively and injects a Bearer header only from the supplied
`AuthSession`. Clearing the session removes authentication from subsequent
requests. No login endpoint, credential form submission, refresh workflow, or
frontend authorization substitute was added.

## HTTP timeout and cancellation behavior

- Every request has an internal `AbortController` and timer.
- Default timeout: 10,000 ms.
- Allowed timeout range: 1 through 30,000 ms.
- Caller cancellation and timeout use first-event-wins classification.
- Already-aborted caller signals fail before fetch.
- Fetch adapters that ignore abort are still bounded by an internal
  `Promise.race`.
- Timers and external abort listeners are removed after settled requests.
- Absolute, root-relative, scheme-bearing, empty, fragment-bearing,
  backslash-bearing, parent-traversal, encoded traversal, and encoded separator
  paths are rejected so a call cannot escape the canonical base.

## Canonical envelope and error mapping

Success requires both a successful HTTP status and exactly a canonical
`success: true` envelope containing `data`. Canonical failures require a
non-success HTTP status and `success: false` with non-empty string `code` and
`message`. Invalid JSON, mismatched status/envelope pairs, and malformed
envelopes fail closed as `protocol / invalid_response_envelope`.

| Condition | Frontend kind |
| --- | --- |
| HTTP 401 | `authentication` |
| HTTP 403 | `permission` |
| HTTP 400 | `validation` |
| HTTP 409 | `conflict` |
| HTTP 404 | `not_found` |
| Internal timeout | `timeout` |
| Caller abort | `cancelled` |
| Fetch/network exception | `network` with generic message |
| Other HTTP failure | `server` |
| Malformed response/config/path/auth/header | `protocol` |

Backend response data is not transformed into business decisions. Exact backend
permission and domain enforcement remains authoritative.

## Focused test matrix and exact results

Command: `pnpm --dir figma_make_frontend run test`

Result: **12 passed, 0 failed, 0 cancelled, 0 skipped** in 260.0318 ms.

| Test group | Evidence |
| --- | --- |
| Base URL | Default/config normalization and rejection of scheme-relative, relative, prefixed, credentialed, non-HTTP(S), query, fragment, and non-canonical bases. |
| Authentication | Session-only Bearer injection, caller header override prevention across header shapes, clear behavior, malformed-token rejection, auth-session error redaction. |
| Envelope parsing | Typed success data, malformed envelopes, HTTP/envelope mismatches, whitespace-only error fields, and invalid JSON redaction. |
| Error mapping | Authentication, permission, validation, conflict, not-found, and server classifications. |
| Failure control | Timeout, caller cancellation, generic network error, first abort reason, ignored-abort bounding, and already-aborted no-fetch behavior. |
| Cleanup | External abort listener removal and timeout clearing after settled request. |
| Bounds/isolation | Timeout range enforcement, path escape rejection, query retention without base escape, no retries, and no browser storage/console usage. |

No live HTTP request or business form submission occurred; all responses came
from injected deterministic fetch functions.

## Frontend type, format, lint, and build results

| Check | Exact result |
| --- | --- |
| `pnpm --dir figma_make_frontend run typecheck` | Passed using strict `tsconfig.phase5a.json` for `src/api/**/*.ts`. |
| `pnpm --dir figma_make_frontend run test` | Passed: 12/12 in 260.0318 ms. |
| `figma_make_frontend\node_modules\.bin\oxfmt.cmd figma_make_frontend\src\api\canonical.ts figma_make_frontend\src\api\canonical.test.ts` | Passed; both files unchanged. |
| `pnpm --dir figma_make_frontend run build` | Passed with Vite 8.0.5; 16 modules transformed in 225 ms. |
| Whole-app `figma_make_frontend\node_modules\.bin\tsc.cmd --noEmit -p figma_make_frontend\tsconfig.json` | Failed on five pre-existing malformed inline prop-type declarations in untouched `src/App.tsx` lines 59, 99, 154, 927, 1108. |
| Lint | No lint script or lint configuration exists. |
| Docker/PostgreSQL/Django suites | Not run because Phase 5A has no backend or database change. |

`figma_make_frontend/src/App.tsx` remains byte-identical to HEAD by Git blob
evidence: worktree blob and `HEAD:figma_make_frontend/src/App.tsx` both equal
`deed5a21d32b78491dfcfbaa975a427a5e93d40b`.

## Secret-materialization and diff inspection

A scoped scan of every Phase 5A frontend implementation/config/test path found
no browser storage access, cookie access, console output, password/API-key
literal, token-shaped Bearer value, or authorization logging/printing. Test
auth uses a short non-credential sentinel only to assert header ownership.

The changed-path inspection confirmed:

- no hard-coded credential or realistic mock credential;
- no raw request headers, raw response bodies, or fetch exception details are
  exposed through client errors;
- no screen silently falls back from a canonical request to mocks because no
  screen is connected yet;
- no backend state machine, totals, permission matrix, or other business rule is
  duplicated;
- no permissive CORS, CSRF, middleware, endpoint, binding, AI Factory, n8n,
  Zalo, 9Router, Codex Bridge, or port change;
- no generated artifact included.

## Compatibility evidence

- `App.tsx`, visual components, CSS, and mock data have no content diff from
  HEAD.
- The production application build passes.
- The canonical client is unreferenced by existing screens, so their runtime
  data and navigation behavior are unchanged.
- No backend code changed; Phase 3/4 behavior, exact permissions, write
  boundaries, locks, transactions, audit evidence, and legacy routes remain
  untouched.

## Current SHA256 manifest

| Path | SHA256 |
| --- | --- |
| `figma_make_frontend/package.json` | `95325092CB961F6D136F0780AE45C6C443898B52FA6D6BA612F14FC249D600D4` |
| `figma_make_frontend/tsconfig.phase5a.json` | `6514EB30B34E1768EAE10C57D4AE6518437B8E1DDDCB73334CAE8A5AE02715DF` |
| `figma_make_frontend/src/api/canonical.ts` | `93EC49F24C562BBB802AA8A26CC88BC317B76BC4CA8FCB28873CFF247767685D` |
| `figma_make_frontend/src/api/canonical.test.ts` | `19D3EF140B09FA96F2CE02E05EB1B13E9B3B263F8B0D1ADA37B70EAFA1088B5C` |
| `PHASE_5_SCOPE_DISCOVERY_AND_IMPLEMENTATION_PLAN.md` | `1F63DA709D0907CC04DA6D42AC8421E72D4258285C890F70C792E9A84E3D80B5` |

This report's digest is reported in the final handoff rather than embedded in
itself.

## Git diff stat and final status

Tracked `git diff --stat` before untracked files are added to Git's index:

```text
 figma_make_frontend/package.json | 4 +++-
 1 file changed, 3 insertions(+), 1 deletion(-)
```

Expected final `git status --short`:

```text
 M figma_make_frontend/package.json
?? PHASE_5A_CANONICAL_FRONTEND_FOUNDATION_IMPLEMENTATION_REPORT.md
?? PHASE_5A_INDEPENDENT_REVIEW_AND_REPAIR_REPORT.md
?? PHASE_5_SCOPE_DISCOVERY_AND_IMPLEMENTATION_PLAN.md
?? figma_make_frontend/src/api/
?? figma_make_frontend/tsconfig.phase5a.json
```

No commit was created.

## Phase 5B prerequisites

Before Phase 5B integrates screens, the Owner should choose the exact first
screen/API slice and define token acquisition, expiry/rotation, logout, profile,
loading, empty, permission-denied, validation, conflict, and server-error
acceptance behavior. Whole-app TypeScript also requires the pre-existing
`src/App.tsx` parser/type issues to be repaired or explicitly accepted as
baseline debt before enforcing project-wide `tsc`.
