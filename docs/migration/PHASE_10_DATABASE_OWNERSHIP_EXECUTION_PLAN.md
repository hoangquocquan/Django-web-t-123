# Phase 10 Database Ownership Execution Plan

## Objective

Move Django from read-only legacy database consumer to database owner only after
all gates are approved.

## Safe Work Completed In This Phase

- Created a dependency gate report.
- Created a row-count baseline.
- Added a read-only snapshot script.
- Added test coverage for the snapshot script.

## Ownership Migration Sequence

1. Complete Phase 10.1 PostgreSQL schema design.
2. Complete Phase 10.2 database dry-run migration.
3. Complete Phase 10.3 reconciliation.
4. Execute Phase 10.4 production cutover only after review approval.

## Target Environment

Production PostgreSQL is not configured in this phase. The current Django
`DATABASE_URL` parser already supports PostgreSQL URLs, but no production
connection or secret is added here.

## Managed Model Strategy

Do not flip existing read-only unmanaged models directly. Use approved Phase
10.1 schema design to decide whether each module keeps model names, splits
models, or introduces new managed models.

## Data Migration Strategy

- Read from SQLite backup, not live production file during dry-run.
- Import in dependency order: Catalog, CRM, Sales, CMS, Accounts.
- Validate row counts after each domain.
- Validate foreign keys before enabling writes.

## Validation Strategy

- `python manage.py check`
- `pytest`
- `scripts/phase10_readiness_snapshot.py`
- row-count comparison
- relationship validation
- API response comparison

## Cutover Rule

No production database ownership switch is allowed until Phase 10.4.
