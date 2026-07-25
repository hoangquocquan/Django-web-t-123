# Phase 10.2.1 - PostgreSQL Dry Run Environment Setup

## Project

mecprecision-vietnam

## Objective

Prepare a safe non-production PostgreSQL environment for Phase 10.2 dry-run
migration execution.

Goal:

- Enable controlled PostgreSQL migration simulation.
- Do not touch production.
- Do not modify the legacy SQLite database.
- Do not execute real database ownership transfer.

## Status

Completed:

- Phase 10 - Database Ownership Control Gate
- Phase 10.1 - PostgreSQL Schema Design
- Phase 10.2 - Database Dry Run Migration Gate

Current blocker:

- `PHASE10_DRY_RUN_DATABASE_URL` is not configured.

## Important Rules

Do not:

- migrate production database
- modify production environment
- write to legacy SQLite database
- execute real ownership transfer
- generate production Django migrations
- delete legacy data

Only:

- create test PostgreSQL environment
- configure dry-run connection
- validate connectivity
- document setup process

## Required Documents

Read before implementation:

- `docs/migration/POSTGRESQL_SCHEMA_DESIGN.md`
- `docs/migration/DATABASE_DRY_RUN_REPORT.md`
- `docs/migration/PHASE_10_PREPARATION_PLAN.md`
- `docs/migration/COMPOSITE_KEY_STRATEGY.md`
- `docs/testing/PHASE_TESTING_STANDARD.md`

## Tasks

1. Create PostgreSQL dry-run environment documentation.
2. Create `.env.dryrun.example`.
3. Create `scripts/check_phase10_postgres_connection.py`.
4. Update `scripts/phase10_dry_run_migration.py` safety validation.
5. Create setup guide.
6. Run validation commands.
7. Create review package.

## Git Requirements

Branch:

```text
migration/phase-10.2.1-postgresql-dryrun-environment
```

Commit:

```text
chore: setup postgresql dry run environment
```

Tag:

```text
phase-10.2.1-dryrun-environment-ready
```

## Final Status

WAITING FOR ARCHITECT REVIEW

Do not start Phase 10.3.
