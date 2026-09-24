# Django Multi Database Strategy

Phase: 3.2 - ORM Implementation Readiness & Legacy Database Integration Design  
Rule: Documentation only. No settings code, models, routers, or migrations are created in this phase.

## 1. Purpose

Phase 4 needs Django to read the legacy SQLite database while keeping Django's own internal database separate.

Recommended database aliases:

```text
default = Django internal database
legacy  = existing SQLite database
```

## 2. Database Separation

### default

Purpose:

- Django migrations.
- Django system tables.
- Django auth/session/admin tables if used by Django itself in future.
- Test-only Django framework tables.

Rules:

- Django may own this database.
- Django migrations can run here when approved.
- This database must not contain legacy business data unless a future migration approves it.

### legacy

Purpose:

- Existing SQLite legacy database.
- Unmanaged models.
- Read-only access.
- Parity validation against legacy repositories.

Rules:

- No Django migrations.
- No schema changes.
- No writes in Phase 4.
- No business ownership transfer.

## 3. Future DATABASE_ROUTERS Design

Future router concept:

```text
Legacy unmanaged models
  -> read from "legacy"

Django internal models
  -> read/write from "default"
```

Routing rules:

| Operation | Rule |
|---|---|
| Read unmanaged legacy model | Route to `legacy` |
| Write unmanaged legacy model | Block |
| Migrations for legacy app | Block |
| Django internal migrations | Route to `default` |
| Tests with copied legacy DB | Route `legacy` alias to copy |

## 4. Transaction Boundaries

Phase 4 should not create write transactions against `legacy`.

Read-only queries:

```text
service/repository adapter
  -> using("legacy")
  -> unmanaged model query
```

Do not mix write operations across `default` and `legacy` in Phase 4.

Future write phases must explicitly define:

- transaction owner,
- rollback behavior,
- side effects,
- audit logging,
- fallback to legacy backend.

## 5. Safety Rules

- Never run `migrate --database legacy`.
- Never run `makemigrations` for unmanaged legacy models.
- Do not create Django-managed legacy tables.
- Do not use Django admin write pages for legacy models.
- Do not allow API serializers to call `.save()` on legacy models.
- Test database must use a copy, not the live legacy SQLite file.

## 6. Recommended Configuration Direction

Future settings should support:

```env
DATABASE_URL=
LEGACY_DATABASE_URL=sqlite:///../backend/database/mecprecision.sqlite
```

Where:

- `DATABASE_URL` is Django internal/default.
- `LEGACY_DATABASE_URL` points to legacy SQLite or a copied test database.

## 7. Rollback

Rollback is simple while read-only:

- disable router,
- disable `legacy` database alias,
- disable legacy model import,
- route reads back to legacy repository/API behavior.

No data restore is required if write protection worked.
