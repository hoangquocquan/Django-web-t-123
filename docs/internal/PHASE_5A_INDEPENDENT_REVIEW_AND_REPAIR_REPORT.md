# Phase 5A Independent Review and Targeted Repair Report

## Final verdict

`READY_FOR_PHASE_5A_CHECKPOINT`

Independent review found repairable issues in the first Phase 5A frontend
client. The repairs are complete, focused, and verified. Phase 5A remains a
transport/authentication foundation only; no business screen, backend endpoint,
database, AI Factory/n8n/Zalo/9Router/Codex Bridge surface, or port binding was
changed.

## Baseline and scope confirmation

| Item | Verified value |
| --- | --- |
| Project root | `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO` |
| Repository | `Django-web-t-123` |
| Remote | `https://github.com/hoangquocquan/Django-web-t-123.git` |
| Branch | `codex/demo-database-validation` |
| HEAD | `27002cbf830285f261dda91f1e8b39cd6d72ed3b` |
| Subject | `phase4d: add order progress audit command APIs` |
| Parent | `86e2a0f669acd05764ab05bdf1ec7c64524cab16` |
| Authoritative Phase 5A report pre-review hash | `D9CF321C3C8FED188A4B89A44DB8372EAFDA7C2EC04E975E4D473AC845A1B91F` |

The authorized working set at review start matched the expected Phase 5A files:
`figma_make_frontend/package.json`, the Phase 5 scope plan, the Phase 5A
implementation report, `figma_make_frontend/src/api/canonical.ts`,
`figma_make_frontend/src/api/canonical.test.ts`, and
`figma_make_frontend/tsconfig.phase5a.json`.

## Review findings repaired

1. **High - request lifecycle could misclassify or fail to bound some abort
   races.** Header/auth/path failures were prepared after timer/listener setup,
   and a mutable timeout flag could misclassify caller abort versus timeout in
   close races. A custom fetch adapter that ignored abort could also outlive the
   configured timeout. Repaired by preparing URL/headers/auth before lifecycle
   setup, using first-event-wins abort classification, rejecting already-aborted
   caller signals before fetch, and racing fetch against an internal abort
   promise.

2. **Medium - canonical base/path validation accepted edge forms that could
   confuse the boundary.** Scheme-relative bases, relative suffixes, prefixed
   absolute paths, fragments, backslashes, encoded traversal, and encoded
   separators were not all rejected. Repaired by allowing only exact
   `/api/v1/canonical/` root-relative or HTTP(S) absolute bases and by rejecting
   unsafe request paths before URL construction.

3. **Medium - auth/header ownership needed stricter runtime validation.**
   Custom auth sessions could return malformed token values, and raw auth
   session diagnostics could leak if preparation failed. Repaired by validating
   bearer-token shape at session set and request time, stripping caller
   authorization across header shapes, and converting auth/header preparation
   failures to controlled protocol errors.

4. **Low - test coverage did not yet prove the hardening guarantees.** Repaired
   by expanding the deterministic Node suite from 6 groups to 12 tests covering
   malformed bases, header shapes, invalid tokens, auth-session redaction,
   HTTP/envelope mismatches, invalid JSON redaction, first abort reason, ignored
   abort bounding, already-aborted no-fetch, listener/timer cleanup, path escape
   cases, no retries, and browser storage/console absence.

No finding required backend, database, Django, Docker, UI, or mock-data changes.

## Repair summary by file

| Path | Review repair |
| --- | --- |
| `figma_make_frontend/src/api/canonical.ts` | Hardened base/path validation, token validation, header/auth preparation, first abort reason, timeout bounding, and cleanup. |
| `figma_make_frontend/src/api/canonical.test.ts` | Expanded focused tests to cover the repaired security and lifecycle cases. |
| `PHASE_5A_CANONICAL_FRONTEND_FOUNDATION_IMPLEMENTATION_REPORT.md` | Updated stale test counts, hashes, final verdict, repair evidence, and Phase 5B prerequisites. |
| `PHASE_5A_INDEPENDENT_REVIEW_AND_REPAIR_REPORT.md` | Added this independent review and repair artifact. |

The existing `package.json`, `tsconfig.phase5a.json`, and Phase 5 scope plan
remain semantically unchanged by the repair.

## Validation evidence after repair

| Check | Result |
| --- | --- |
| `pnpm --dir figma_make_frontend run typecheck` | Passed. |
| `pnpm --dir figma_make_frontend run test` | Passed: 12 tests, 0 failures, 260.0318 ms. |
| `figma_make_frontend\node_modules\.bin\oxfmt.cmd figma_make_frontend\src\api\canonical.ts figma_make_frontend\src\api\canonical.test.ts` | Passed; both files unchanged. |
| `pnpm --dir figma_make_frontend run build` | Passed; Vite 8.0.5, 16 modules transformed, built in 225 ms. |
| `git diff --check` | Passed; only line-ending warning for tracked `package.json`. |
| Whole-app `figma_make_frontend\node_modules\.bin\tsc.cmd --noEmit -p figma_make_frontend\tsconfig.json` | Failed only on pre-existing untouched `src/App.tsx` parser errors at lines 59, 99, 154, 927, and 1108. |

Docker, PostgreSQL, and Django suites were not run because Phase 5A did not
change backend, database, migrations, API views, serializers, permissions,
settings, CORS, CSRF, middleware, or ports.

## App and backend preservation proof

- `figma_make_frontend/src/App.tsx` worktree blob:
  `deed5a21d32b78491dfcfbaa975a427a5e93d40b`.
- `HEAD:figma_make_frontend/src/App.tsx` blob:
  `deed5a21d32b78491dfcfbaa975a427a5e93d40b`.
- `git diff --name-only` reports only tracked `figma_make_frontend/package.json`;
  the new client, tests, config, and reports are untracked Phase 5A files.
- No backend/config/status path appears in the diff.
- No generated `dist/` artifact appears in Git status.

## Current SHA256 manifest

| Path | SHA256 |
| --- | --- |
| `figma_make_frontend/package.json` | `95325092CB961F6D136F0780AE45C6C443898B52FA6D6BA612F14FC249D600D4` |
| `figma_make_frontend/tsconfig.phase5a.json` | `6514EB30B34E1768EAE10C57D4AE6518437B8E1DDDCB73334CAE8A5AE02715DF` |
| `figma_make_frontend/src/api/canonical.ts` | `93EC49F24C562BBB802AA8A26CC88BC317B76BC4CA8FCB28873CFF247767685D` |
| `figma_make_frontend/src/api/canonical.test.ts` | `19D3EF140B09FA96F2CE02E05EB1B13E9B3B263F8B0D1ADA37B70EAFA1088B5C` |
| `PHASE_5_SCOPE_DISCOVERY_AND_IMPLEMENTATION_PLAN.md` | `1F63DA709D0907CC04DA6D42AC8421E72D4258285C890F70C792E9A84E3D80B5` |
| `PHASE_5A_CANONICAL_FRONTEND_FOUNDATION_IMPLEMENTATION_REPORT.md` | Report digest intentionally omitted from itself; use final handoff hash. |
| `PHASE_5A_INDEPENDENT_REVIEW_AND_REPAIR_REPORT.md` | Report digest intentionally omitted from itself; use final handoff hash. |

## Final Git status expectation

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

Phase 5B should not start as an implementation task until the Owner selects the
first screen/API slice and defines token acquisition, expiry/rotation, logout,
profile, loading, empty, validation, permission-denied, conflict, and
server-error acceptance behavior. Before project-wide TypeScript can be used as
a hard gate, the existing `src/App.tsx` parser/type debt must also be repaired
or explicitly accepted as baseline debt outside Phase 5A.
