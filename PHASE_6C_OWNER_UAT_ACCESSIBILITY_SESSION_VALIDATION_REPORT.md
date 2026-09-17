# Phase 6C Owner UAT, Accessibility, and Session Validation Report

Date: 2026-09-17 (Asia/Tokyo)

## Scope and boundaries

Validation stayed within the canonical Phase 6 frontend, its focused tests, the
bounded fictional Phase 6B fixture, and the Phase 6C Owner UAT runner. No Phase
6D work, deployment, token persistence, legacy business write route, Docker
prune, unrelated-container mutation, staging, commit, or push was performed.

The working tree already contained uncommitted Phase 5/6 work. That work was
preserved; no reset, restore, clean, or stash was used.

## Root causes and repairs

### Canonical workflow accessibility

The RFQ, quotation, and order workspaces did not consistently expose visible
keyboard focus, stable accessible names, announced async status/error text, or
semantic RFQ row activation. The patch adds focus-visible styling, labels for
form controls, polite/assertive live regions, column scopes, pressed-state
semantics for workspace tabs, and a keyboard-operable RFQ selection button.

### Session and role UAT coverage

The existing automated suites did not exercise browser back/forward navigation,
hard-refresh memory-session loss, cross-role mutable-state isolation, responsive
layouts, 200% zoom, or a runtime accessible-name audit together. A focused
Selenium Owner UAT now covers Sales, Manager, and Admin boundaries without
persisting credentials or bearer tokens.

### Idempotent fictional fixture

Repeated negative-login validation could leave failed login-attempt rows for the
fictional Phase 6B accounts and eventually lock a later UAT login even though the
fixture refreshed the users. The fixture now removes only failed attempts whose
privacy hashes belong to its three `.invalid` identities. Successful history and
unrelated identities remain untouched. A regression test proves the cleanup is
bounded and idempotent.

### Browser harness false timeout

The Phase 6C helper compared Selenium's rendered button text with mixed-case DOM
labels. CSS `text-transform: uppercase` changed the rendered value, so a
successful login (Django returned HTTP 200) was reported as a timeout. The helper
now compares normalized DOM `textContent`. Login navigation also excludes
`#/admin-login` explicitly instead of accepting it as a substring match for
`#/admin`.

## Files changed for Phase 6C

- `figma_make_frontend/src/App.tsx`
- `figma_make_frontend/src/components/RfqWorkspace.tsx`
- `figma_make_frontend/src/components/QuotationWorkspace.tsx`
- `figma_make_frontend/src/components/OrderWorkspace.tsx`
- `figma_make_frontend/src/api/phase6c.test.ts`
- `figma_make_frontend/package.json`
- `tests/e2e/phase6b_canonical_browser_e2e.py`
- `tests/e2e/phase6c_owner_uat.py`
- `django_backend/apps/core/management/commands/phase6b_e2e_fixture.py`
- `django_backend/apps/core/tests/test_phase6b_e2e_fixture.py`
- `PHASE_6C_OWNER_UAT_ACCESSIBILITY_SESSION_VALIDATION_REPORT.md`

Some tracked files above also contain earlier uncommitted Phase 6B work. This
report does not attribute pre-existing worktree changes to Phase 6C.

## Tests added and live Owner UAT evidence

- Five focused frontend checks cover live regions and sanitized errors,
  accessible form names, keyboard focus, semantic RFQ selection, responsive and
  session/role UAT coverage, memory-only auth, and canonical-only write bounds.
- The fixture test now proves failed attempts for fixture identities are removed,
  successful attempts are retained, and two fixture executions remain safe.
- The Selenium UAT proved:
  - invalid login feedback is sanitized and the password field is cleared;
  - Sales can reach canonical selector/RFQ authoring controls but not Manager
    review controls;
  - visible canonical controls have accessible names;
  - keyboard focus reaches a visibly focused button;
  - 1440x1000, 1024x768, 768x900, and 1024x768 at 200% zoom have no page-level
    horizontal overflow;
  - back/forward hash navigation keeps the in-memory session;
  - hard refresh loses the bearer session;
  - re-login starts with cleared mutable RFQ form state;
  - Manager cannot create an RFQ and can access global audit refresh;
  - Admin retains the intended RFQ capability;
  - mutable Sales/Manager state does not leak across role switches.

Live runner result:

```text
PHASE6C_OWNER_UAT_PASS accessible_names=pass focus=BUTTON layouts=4 session_boundary=pass roles=pass
```

The fixture was applied via stdin and reported
`PHASE6B_FIXTURE_READY users=3 customer_id=1 material_id=1 part_id=1`. No
password or bearer token was printed or persisted.

## Exact validation results

- `pnpm run test:phase6c`: PASS, 5/5.
- `pnpm run test`: PASS, 142/142.
- `pnpm run typecheck`: PASS.
- `pnpm run build`: PASS, Vite production build completed.
- Focused fixture test: PASS, 3/3.
- `python manage.py check`: PASS, zero issues.
- `python manage.py makemigrations --check --dry-run`: PASS, no changes detected.
- Ruff lint on the fixture and browser runners: PASS.
- Ruff format check on the fixture and browser runners: PASS, four files.
- Oxfmt check on the touched frontend files: PASS.
- `git diff --check`: PASS; Git emitted only line-ending conversion warnings.
- Direct Django liveness on `8001`: PASS (`success=true`, `status=live`).
- Vite root-relative `/api` proxy on `8443`: PASS
  (`success=true`, `status=live`).
- Phase 6 readiness endpoint: PASS (`success=true`).

## Runtime coexistence and cleanup

The Phase 6 stack ran with Django on `127.0.0.1:8001` and Vite on
`127.0.0.1:8443`. Cleanup used only
`scripts/phase6/Stop-Phase6.ps1`; it removed only resources owned by
`django-web-t-123-phase6`.

After cleanup:

- no Phase 6 container remained;
- host ports `8001` and `8443` had zero listeners;
- unrelated container `mecprecision-vietnam-web-1` remained healthy with the
  same container id `dfd724919eb2`, image `mecprecision-vietnam:prod-local`, and
  host publication `8000->8000`.

## Security and release boundary confirmation

No `localStorage`, `sessionStorage`, IndexedDB, cookie-based token persistence,
credential logging, bearer-token logging, legacy write route, or unrelated
business mutation was introduced. No migration was created. Nothing was staged,
committed, pushed, deployed, or started for Phase 6D.

## Remaining blockers

None for the authorized Phase 6C scope.

## Final verdict

PASS_PHASE_6C_OWNER_UAT_ACCESSIBILITY_SESSION_VALIDATION
