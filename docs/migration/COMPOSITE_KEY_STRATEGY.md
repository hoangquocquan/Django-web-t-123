# Composite Key Strategy

Phase: 3.1 - Database Mapping Hardening & ORM Preparation Rules  
Rule: Documentation only. No Django models, migrations, or database changes.

## 1. Purpose

This document defines how to handle legacy SQLite tables that use composite primary keys or behave as junction tables.

Django's standard ORM works best with a single primary key field. The legacy database has several link tables where the real identity is a pair of foreign keys.

## 2. Global Decision

Preferred Phase 4 strategy:

```text
Use unmanaged explicit link models.
```

Required Meta behavior:

```python
class Meta:
    managed = False
    db_table = "legacy_link_table"
```

Do not introduce a third-party composite key package unless explicitly approved.

Do not modify the database to add surrogate IDs in Phase 4.

## 3. Composite / Junction Tables

| Table | Current PK | Relationship Type | Problem | Recommended Django Approach |
|---|---|---|---|---|
| `product_materials` | `product_id`, `material_id` | Product to material many-to-many | Composite PK is not a normal single Django PK | Use unmanaged `ProductMaterial` through model; preserve both FK columns; validate uniqueness. |
| `product_processes` | `product_id`, `process_id` | Product to process many-to-many with extra fields | Has extra fields `step_order` and `note`; not a simple auto M2M | Use unmanaged `ProductProcess` through model; keep extra fields; validate workflow ordering. |
| `capability_machines` | `capability_id`, `machine_id` | Capability to machine many-to-many | Composite PK junction table | Use unmanaged `CapabilityMachine` through model; preserve both FK columns. |
| `news_tags` | `news_id`, `tag_id` | News to tag many-to-many | Composite PK junction table | Use unmanaged `NewsTag` through model; preserve both FK columns. |

## 4. Detailed Table Notes

### product_materials

Current PK:

```text
product_id + material_id
```

Problem:

- Django normally expects one primary key field.
- The table is a pure relationship table.

Recommended Django approach:

- Future model name: `ProductMaterial`
- App: `catalog`
- `managed = False`
- `db_table = "product_materials"`
- Treat as explicit through model between `Product` and `Material`.
- Do not add an `id` column.

### product_processes

Current PK:

```text
product_id + process_id
```

Problem:

- Composite PK.
- Contains extra relationship fields: `step_order`, `note`.
- Order matters for process workflow.

Recommended Django approach:

- Future model name: `ProductProcess`
- App: `catalog`
- `managed = False`
- Preserve both FK columns.
- Preserve `step_order` as the workflow ordering field.
- Do not use automatic `ManyToManyField` without a through model.

### capability_machines

Current PK:

```text
capability_id + machine_id
```

Problem:

- Composite PK pure junction table.

Recommended Django approach:

- Future model name: `CapabilityMachine`
- App: `catalog`
- `managed = False`
- Use explicit through model between `Capability` and `Machine`.

### news_tags

Current PK:

```text
news_id + tag_id
```

Problem:

- Composite PK pure junction table.

Recommended Django approach:

- Future model name: `NewsTag`
- App: `content`
- `managed = False`
- Use explicit through model between `NewsArticle` and `Tag`.

## 5. Validation Requirements

For every composite/link table:

- Validate row count.
- Validate no duplicate pairs.
- Validate every FK points to an existing parent.
- Validate API/list output remains unchanged.
- Validate delete behavior before enabling any write/admin workflow.

## 6. Rejected Options For Phase 4

Rejected unless explicitly approved:

- Adding new surrogate `id` columns to legacy tables.
- Converting tables to Django-managed migrations.
- Installing a third-party composite primary key package.
- Replacing link tables with automatic Django-created M2M tables.

## 7. Future Ownership Decision

If the project later moves to PostgreSQL or Django-managed schema, the team can revisit whether to:

- keep composite keys,
- add surrogate IDs,
- convert to Django-managed M2M through models,
- normalize extra relationship fields.

That decision is outside Phase 4.

## 8. Phase 10.1 PostgreSQL Ownership Decision

Phase 10.1 revisits the future ownership decision for the currently mapped
catalog link tables.

Target PostgreSQL decision:

```text
Use surrogate `id` primary keys on Django-managed link tables.
Preserve legacy pair identity with unique constraints.
```

Reason:

- Django managed models and admin workflows are simpler with one primary key.
- PostgreSQL can still enforce the original pair uniqueness.
- Data reconciliation remains clear because the original FK pairs are preserved.
- Future APIs can refer to link rows consistently if write workflows are added.

## 9. Phase 10.1 Target Table Rules

| Table | Target primary key | Required unique constraint | Notes |
|---|---|---|---|
| `product_materials` | new surrogate `id` | unique `(product_id, material_id)` | preserve product/material identity |
| `product_processes` | new surrogate `id` | unique `(product_id, process_id)` | preserve `step_order` and `note` |
| `capability_machines` | new surrogate `id` | unique `(capability_id, machine_id)` | preserve capability/machine identity |

## 10. Migration Validation

Before adding surrogate IDs in a dry-run migration:

- confirm no duplicate FK pairs exist,
- confirm every FK points to an existing parent row,
- import the original FK columns unchanged,
- compare row counts before and after import,
- verify APIs return the same product/capability relationships.

## 11. Rejected For Phase 10.1

- Keeping composite primary keys as the managed Django target.
- Dropping link tables in favor of implicit Django many-to-many tables.
- Removing relationship metadata such as `step_order` or `note`.
- Changing production data before a dry run is approved.
