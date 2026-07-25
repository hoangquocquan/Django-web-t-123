# Data Ownership Matrix

## Current Ownership

All migrated modules currently read from legacy SQLite. Legacy remains the data
owner and Django is a read-only consumer.

## Future Ownership Target

Future ownership means Django-managed database tables become the source of
truth after a reviewed Phase 10 migration.

| Domain | Current owner | Current Django mode | Future owner | Future Django mode | Ownership migration note |
|---|---|---|---|---|---|
| Catalog | Legacy SQLite/backend | read-only unmanaged | Django | managed models | migrate first because Sales depends on products/materials |
| CRM | Legacy SQLite/backend | read-only unmanaged | Django | managed models | migrate before Sales; define contact/customer matching separately |
| Sales | Legacy SQLite/backend | read-only unmanaged | Django | managed models | migrate after Catalog and CRM; preserve quote snapshot semantics |
| CMS | Legacy SQLite/backend | read-only unmanaged | Django | managed models | migrate after content/menu validation; preserve nested menu tree |
| Accounts | Legacy SQLite/backend | read-only unmanaged | Django after security approval | managed models or dedicated auth design | highest security risk; do not migrate before auth cutover review |

## Ownership Rules

- No module changes owner without backup, validation and rollback plan.
- No write API is enabled until its module owns data safely.
- Accounts ownership requires separate security review.
- API layer should remain independent of database ownership details.
