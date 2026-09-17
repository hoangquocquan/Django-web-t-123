# Phase 6B canonical browser E2E

This local-only run targets the Phase 6 PostgreSQL stack through Vite at
`http://127.0.0.1:8443`. It does not use legacy write routes.

## Bounded fictional fixture

`python manage.py phase6b_e2e_fixture --password-stdin` reads one local password
without echoing or accepting it on the command line. The command is idempotent
and creates or refreshes only these records:

- users: `phase6b.admin@example.invalid`, `phase6b.sales@example.invalid`,
  `phase6b.manager@example.invalid`;
- customer: `CUS-PHASE6B-E2E` / `Phase 6B Fictional Robotics`;
- material: `MAT-PHASE6B-E2E` / `Phase 6B Fictional SUS304`;
- part: `PART-PHASE6B-E2E` / `Phase 6B Fictional Precision Bracket`.

The command seeds identity and selector master data only. RFQs, RFQ lines,
quotations, orders, progress events, and audit events are created by canonical
browser API actions. Each browser run tags its RFQ project as
`PHASE6B-E2E-<random suffix>`.

Canonical orders, progress history, and audit evidence are intentionally
immutable/append-only. Therefore Phase 6B does not provide or run a cleanup
that bypasses those domain protections. Test-created workflow records remain
clearly bounded by the project prefix and fictional master-data codes.

## Runner

Set `PHASE6B_E2E_PASSWORD` only in the current process, seed the fixture through
stdin, then run:

```powershell
python tests/e2e/phase6b_canonical_browser_e2e.py
```

The runner uses the repository's existing Selenium dependency and local Chrome,
so no frontend browser framework is added. It never prints the password or
browser bearer token. It performs a hard refresh after RFQ creation to verify
that the memory-only session is cleared, then logs in again and proves exactly
one matching RFQ exists before continuing.
