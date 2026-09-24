# Phase 3.1 Review Summary

## Objective

Resolve remaining database architecture decisions before Phase 4: Read-Only Django ORM Models.

This phase hardens the mapping rules only.

No Django models were created.
No migrations were created or run.
No SQLite database changes were made.
No legacy backend code was modified.
No API endpoints were created.
No authentication migration was performed.

## Issues Resolved

- Defined future ORM model naming convention.
- Defined table mapping rules for unmanaged models.
- Defined SQLite-to-Django field mapping rules.
- Defined primary key preservation rules.
- Defined relationship and foreign key rules.
- Defined composite key/junction table strategy.
- Defined database view mapping boundary.
- Defined media migration boundary.
- Defined authentication migration boundary.
- Added migration phase and read-only priority guidance to `DATABASE_MAPPING.md`.
- Added read-only ORM flow to `ORM_MAPPING_STRATEGY.md`.

## Documents Created

| Document | Purpose |
|---|---|
| `docs/migration/ORM_MODEL_CONVENTION.md` | Naming, table, field, primary key, and relationship rules for future models |
| `docs/migration/COMPOSITE_KEY_STRATEGY.md` | Strategy for composite primary keys and many-to-many junction tables |
| `docs/migration/DATABASE_VIEW_STRATEGY.md` | Rules for mapping SQLite views as read-only models |
| `docs/migration/MEDIA_MIGRATION_STRATEGY.md` | Boundary that media paths remain text fields in Phase 4 |
| `docs/migration/AUTH_MIGRATION_BOUNDARY.md` | Boundary that auth tables remain read-only and auth behavior is not migrated |

## Architecture Decisions

| Decision | Reason |
|---|---|
| Future legacy models use `managed = False` | Prevents Django from owning or changing legacy tables |
| Preserve legacy primary keys | Keeps existing FK relationships and validation stable |
| Do not add surrogate IDs to composite tables in Phase 4 | Avoids schema changes and migration risk |
| Use explicit through models for junction tables | Keeps many-to-many tables understandable and testable |
| Do not map `product_overview` first | Direct table mapping is safer for initial ORM parity |
| Keep media paths as text | Avoids file/storage migration during ORM phase |
| Keep auth read-only if needed | Avoids security/session/password migration risk |
| No third-party composite key package by default | Reduces dependency and ORM complexity unless approved |

## Database Impact

```text
None
```

The database was not modified.

## ORM Rules Established

Future Phase 4 read-only models must:

- use singular PascalCase names,
- preserve business meaning,
- define `managed = False`,
- define exact `db_table`,
- preserve primary keys,
- keep media paths as text,
- treat composite key tables as unmanaged explicit through models,
- avoid database views unless explicitly approved,
- avoid auth behavior migration.

Approved read-only ORM flow:

```text
Legacy Database
  -> Unmanaged Django Models
  -> Validation
  -> Service Layer
  -> API Migration
```

## Remaining Risks

- Composite key tables still need careful implementation in Phase 4 because Django's normal ORM prefers a single primary key.
- Timestamp fields stored as `TEXT` or epoch-like integers need validation before choosing exact Django field types.
- Auth/session/password tables remain high risk and must not become behavior-changing models.
- Media path fields may contain inconsistent paths or URLs; Phase 4 should not normalize them.
- View-backed models can accidentally be used for writes unless explicitly protected.

## Recommendation

Proceed to Phase 4 only after architecture review approves:

- model convention,
- composite key strategy,
- view strategy,
- media boundary,
- auth boundary,
- Phase 4 slice order.

Recommended next phase:

```text
Phase 4 - Read-Only Unmanaged Django ORM Models
```

Status:

```text
WAITING FOR ARCHITECT REVIEW
```
