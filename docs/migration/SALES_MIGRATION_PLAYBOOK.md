# Sales Migration Playbook

## Objective

Use Phase 6 Sales / Quotation as the standard pattern for future read-only and write-enabled Sales migration work.

## Standard Pattern

```text
Model
  |
  v
Repository
  |
  v
Service
  |
  v
Transaction Boundary
  |
  v
Tests
```

## Model

Rules:

- Inherit `LegacyReadOnlyModel`.
- Use `managed = False`.
- Keep `db_table` exactly matching legacy SQLite.
- Keep file paths and quote values unchanged.
- Do not add snapshot fields until a future schema phase is approved.

## Repository

Rules:

- Query through `.using("legacy")`.
- Keep Sales ORM access inside repository.
- Use `select_related` for customer/product/material.
- Use `prefetch_related` for items and files.

## Service

Rules:

- Depend on repository interface.
- Do not call ORM directly.
- Do not implement workflow status mutation in read-only phases.
- Return quote detail as quote header, items and files.

## Transaction Boundary

Read-only phase:

- No write transaction.
- No `transaction.atomic()` write flow.

Future write phase:

- Wrap quote creation, items and file metadata in one database transaction.
- Keep physical file cleanup outside database rollback but controlled by job/queue.

## Tests

Required tests:

- row count parity,
- repository uses legacy alias,
- quote/customer relationship,
- item/product/material relationship,
- file path preservation,
- read-only protection,
- fixture copy validation,
- query count for list/detail loading.

## Common Mistakes

- Mutating customer records from Sales.
- Mutating product or material records from Sales.
- Treating live product price as historical quote price.
- Moving physical files during ORM migration.
- Creating write APIs before transaction and snapshot decisions are approved.
- Adding status workflow automation before status vocabulary is approved.

## Dependency Rules

CRM owns:

- customer profile,
- customer identity,
- customer merge/link rules.

Catalog owns:

- product master data,
- material master data,
- product pricing source if introduced later.

Sales owns:

- quote lifecycle,
- quote item snapshot,
- quote file metadata,
- quote transaction boundary.
