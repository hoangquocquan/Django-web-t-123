# Legacy Archive Strategy

## Objective

Preserve the legacy system as a read-only archive before any future shutdown.
The archive must support audit, rollback investigation and restore testing.

## Archive Scope

| Item | Include | Notes |
|---|---|---|
| Legacy source | Yes | `backend/` |
| Legacy database | Yes | `backend/database/mecprecision.sqlite` |
| SQL schema and seed | Yes | `backend/database/schema.sql`, `backend/database/seed.sql` |
| Uploads/media | Yes | `backend/uploads/` |
| Logs/audit evidence | Yes | `backend/logs/` and audit-related exports |
| Environment files | Controlled | Do not expose secrets in review packages |
| Backups | Yes | Never delete backups during Phase 11 |

## Security Rules

- Do not commit `.env` files.
- Do not include raw credentials in public review artifacts.
- Store database archives in a protected location.
- Record checksum for every archive file.
- Limit archive restore access to approved operators.

## Restore Verification

Archive restore is not considered valid until:

1. Archive checksum matches the recorded checksum.
2. SQLite database opens successfully.
3. Critical tables can be counted.
4. Upload paths can be listed.
5. Legacy entrypoint can be inspected from the archive.

## Current Archive Status

```text
PENDING
```

No archive was created by this phase. This phase only defines the required
strategy and readiness checks.
