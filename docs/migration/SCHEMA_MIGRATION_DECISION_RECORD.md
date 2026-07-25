# Schema Migration Decision Record

## ID

SMDR-001

## Decision

Design the Phase 10 PostgreSQL target schema as Django-managed tables that
preserve legacy table names and source IDs, while improving constraints,
indexes and field types only where validation supports the change.

## Context

The project currently uses unmanaged read-only Django ORM models against legacy
SQLite. Phase 10.1 is design-only. Production data migration, Django migration
files and PostgreSQL cutover are intentionally out of scope.

## Options Considered

### Option A - Preserve legacy schema exactly

Pros:

- lowest migration transformation risk
- simplest row-count reconciliation

Cons:

- keeps weak text typing
- misses useful PostgreSQL constraints/indexes
- keeps migration-era compromises

### Option B - Fully redesign normalized schema

Pros:

- strongest long-term model
- opportunity to fix historical data issues

Cons:

- high migration risk
- harder rollback
- bigger API compatibility risk

### Option C - Preserve table names and IDs, improve selected constraints and types

Pros:

- safer reconciliation
- keeps API compatibility easier
- enables PostgreSQL indexes/constraints gradually

Cons:

- some legacy compromises remain until later modernization phases

## Selected Option

Option C.

## Decision Reason

Phase 10 must reduce ownership risk. Preserving table names and IDs gives a
clear source-to-target mapping, while selective constraints and indexes give
Django a safer production foundation without forcing a full redesign during
ownership migration.

## Consequences

- Phase 10.2 dry run can compare row counts directly.
- API compatibility is easier to verify.
- Composite link tables receive surrogate IDs in target schema, with unique
  constraints preserving legacy pair identity.
- Auth/session/token ownership remains gated by security approval.

## Required Follow-Up

- Run duplicate and orphan validation before generating migrations.
- Create dry-run PostgreSQL migration.
- Compare API responses before and after import.
- Revisit deeper normalization in Phase 13.

## Status

Proposed for architecture review
