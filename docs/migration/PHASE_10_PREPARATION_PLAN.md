# Phase 10 Preparation Plan

## Objective

Prepare for Database Ownership Migration without starting it in Phase 9.3.

## PostgreSQL Migration Approach

1. Keep legacy SQLite as source of truth during planning.
2. Create managed Django model design proposal per module.
3. Create PostgreSQL target schema in an isolated environment.
4. Run import scripts against a copied SQLite backup.
5. Validate row counts, relationships and API responses.
6. Repeat dry run until deterministic.
7. Only then schedule controlled production cutover.

## Backup Strategy

- Create SQLite file backup before every dry run.
- Store backup with timestamp and checksum.
- Export schema and row counts.
- Preserve uploaded/media file paths separately.
- Keep rollback copy available until post-cutover validation passes.

## Rollback Strategy

Rollback means:

1. Stop routing writes to Django-owned database.
2. Route application traffic back to legacy backend/database.
3. Restore legacy SQLite backup if any write freeze was violated.
4. Compare health/API contract tests again.
5. Document rollback cause and create minor phase correction.

## Migration Order

Recommended order:

1. Catalog reference data
2. CRM customers and contact requests
3. Sales quotation data
4. CMS pages/menu/banner/newsletter
5. Accounts/auth data after security approval

## Validation Steps

- Compare row counts for every table.
- Validate foreign-key relationships.
- Validate unique fields.
- Run Django API tests against migrated target database.
- Run full regression suite.
- Compare representative API responses before/after migration.
- Verify no password/session/token sensitive fields are exposed.

## Cutover Checklist

- [ ] Target PostgreSQL schema approved.
- [ ] Dry-run migration completed.
- [ ] Row-count validation passed.
- [ ] Relationship validation passed.
- [ ] Backup and restore tested.
- [ ] Rollback plan rehearsed.
- [ ] Auth boundary reviewed.
- [ ] API regression passed.
- [ ] Production traffic switch approved.
