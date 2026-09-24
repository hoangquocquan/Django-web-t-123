# Database Connection Strategy

Phase: 3.2 - ORM Implementation Readiness & Legacy Database Integration Design  
Rule: Documentation only. No models, migrations, database writes, or legacy code changes.

## 1. Purpose

This document answers:

```text
How will Django safely read the legacy database?
```

Phase 4 should allow Django to read legacy SQLite tables through unmanaged ORM models without transferring ownership of the database to Django.

## 2. Current Legacy Database

Legacy database:

```text
backend/database/mecprecision.sqlite
```

Engine:

```text
SQLite
```

Phase 4 requirement:

```text
Read-only access to legacy database.
```

## 3. Option A - Django Direct Connection To Legacy SQLite

Connection flow:

```text
Django settings
  -> legacy database alias
  -> backend/database/mecprecision.sqlite
  -> unmanaged Django models
  -> read-only service/repository adapter
```

Advantages:

- Reads the exact same data as the legacy backend.
- Best for parity checks.
- No copy freshness problem.
- No data export/import step.
- Fastest path to validating ORM mappings.

Disadvantages:

- SQLite write-locking risk if any accidental writes happen.
- Requires strong read-only protection in application code.
- Local file path must be configured carefully.
- Tests must avoid modifying the real legacy database.

Risks:

- Accidental write from Django ORM.
- Bad path configuration points Django at the wrong database.
- Concurrent legacy writes while Django reads can produce timing differences.

Rollback:

- Remove/disable the `legacy` database alias.
- Disable Phase 4 unmanaged model imports.
- Keep legacy backend as the only database reader.
- No database restore needed if no writes occurred.

## 4. Option B - Database Copy

Connection flow:

```text
Legacy SQLite
  -> copied SQLite file
  -> Django legacy alias points to copy
  -> unmanaged models
  -> validation
```

Advantages:

- Safer for experimentation.
- No risk of accidental writes to production/local legacy DB.
- Good for tests, CI, and reviewer validation.

Disadvantages:

- Copy can become stale.
- Requires copy/refresh process.
- Cannot validate real-time parity when legacy backend is changing data.
- Extra operational step.

Risks:

- Reviewer/test results differ from current runtime data.
- Copy process accidentally overwrites the real database if scripted poorly.

Rollback:

- Delete copied database file.
- Recreate copy from legacy database.
- No production data restore needed if copy is isolated.

## 5. Option C - Future PostgreSQL Migration

Connection flow:

```text
Legacy SQLite
  -> export/transform
  -> PostgreSQL
  -> Django managed or unmanaged models
```

Advantages:

- Better production concurrency.
- Stronger database permissions.
- Better future scaling and observability.

Disadvantages:

- Much higher migration risk.
- Requires data migration scripts.
- Requires validation/rollback plan.
- Too large for Phase 4.

Risks:

- Data conversion bugs.
- Timestamp/boolean/composite key mismatch.
- Downtime or dual-write complexity.

Rollback:

- Keep SQLite backup.
- Route application back to legacy SQLite.
- Restore records from backup if a migration was partially applied.

## 6. Recommended Direction

Recommended Phase 4 approach:

```text
Option A for local/staging parity:
Django direct read-only connection to legacy SQLite.

Option B for tests/CI:
Django reads a copied SQLite fixture/database.
```

Do not use Option C in Phase 4.

## 7. Required Safety Controls

Before Phase 4 models are implemented:

- Configure separate `legacy` database alias.
- Keep `default` database separate for Django internal tables.
- Use unmanaged models: `managed = False`.
- Add read-only service/repository rules.
- Add tests that prove write operations are blocked.
- Never run migrations against the legacy alias.
- Do not point test writes at `backend/database/mecprecision.sqlite`.

## 8. Rollback Summary

Because Phase 4 should be read-only:

- rollback means disabling Django legacy reads,
- no schema rollback should be needed,
- no data rollback should be needed,
- the legacy backend remains operational.
