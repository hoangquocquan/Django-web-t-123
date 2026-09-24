# ORM Test Strategy

Phase: 3.2 - ORM Implementation Readiness & Legacy Database Integration Design  
Rule: Documentation only. No test implementation in this phase.

## 1. Purpose

This document defines the tests required before and during Phase 4 read-only unmanaged ORM model implementation.

## 2. Connection Test

Goal:

```text
Verify Django can connect to the legacy database.
```

Checks:

- `legacy` database alias exists.
- SQLite file path resolves.
- connection opens in read-only scenario.
- table list can be read.
- no write is performed.

Expected result:

```text
PASS: Django can read table metadata from legacy database.
```

## 3. Model Mapping Test

Goal:

```text
Verify table exists, fields match, and primary key works.
```

For each model:

- table exists,
- model `db_table` matches table,
- expected columns exist,
- nullable/default assumptions match mapping document,
- primary key reads correctly,
- row count can be queried.

## 4. Relationship Test

Goal:

```text
Verify foreign keys and many-to-many relations.
```

Checks:

- foreign key count matches direct SQL,
- parent objects can be resolved,
- composite link tables retain pair uniqueness,
- no orphan relationships for required FK paths,
- relationship ordering fields such as `step_order` are preserved.

## 5. Read-Only Test

Goal:

```text
Verify write operations are blocked.
```

Attempt and expect failure:

- `.save()`,
- `.delete()`,
- queryset `.update()`,
- queryset `.delete()`,
- serializer `.save()` in later API phases.

No test should mutate `backend/database/mecprecision.sqlite`.

## 6. Data Integrity Test

Goal:

```text
Verify count matches legacy database.
```

Checks:

- table count from direct SQLite equals ORM count,
- sample rows match key fields,
- important status fields match,
- boolean fields map correctly,
- timestamp fields do not lose data.

## 7. Repository Parity Test

Goal:

```text
Verify repository adapter output matches legacy repository output.
```

Examples:

- product category list,
- product list,
- product detail with specs/images,
- material/process relationships,
- capability-machine relationships.

## 8. Test Database Rules

Phase 4 tests should prefer:

```text
copied legacy SQLite database
```

Rules:

- never mutate real legacy database,
- test copy can be regenerated,
- expected counts are based on fixture copy,
- read-only tests must prove writes fail.

## 9. Minimum Phase 4A Test Coverage

For catalog slice:

- `ProductCategory` count and slug uniqueness.
- `Material` count and name uniqueness.
- `Machine` count and status values.
- `ManufacturingProcess` count and sort order.
- `Product` count, slug, category FK.
- `ProductImage` and `ProductSpec` child counts.
- `ProductMaterial`, `ProductProcess`, `CapabilityMachine` pair uniqueness.

## 10. Pass Criteria

Phase 4A cannot be considered ready until:

- all connection tests pass,
- all implemented model mapping tests pass,
- relationship tests pass,
- read-only write-block tests pass,
- no migration files are created,
- no SQLite database file changes.
