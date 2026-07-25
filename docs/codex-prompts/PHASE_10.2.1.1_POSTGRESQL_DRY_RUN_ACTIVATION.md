# Phase 10.2.1.1 - PostgreSQL Dry Run Activation & Connection Validation

## Project

mecprecision-vietnam

## Objective

Activate and validate the non-production PostgreSQL dry-run environment required
for Phase 10.2 execution.

Goal:

- A working PostgreSQL dry-run database connection.
- No data import.
- No schema change.
- No Django migration generation.
- No legacy SQLite mutation.

## Current Blocker

PostgreSQL dry-run database is not active and
`PHASE10_DRY_RUN_DATABASE_URL` has not been verified.

## Do Not

- execute migration
- create production database
- migrate legacy data
- modify SQLite
- generate Django migrations
- change application logic

## Only

- activate PostgreSQL test environment
- validate connection
- verify safety rules
- document configuration

## Required Documents

- `docs/migration/POSTGRESQL_DRY_RUN_ENVIRONMENT.md`
- `docs/migration/PHASE_10.2.1_SETUP_GUIDE.md`
- `scripts/check_phase10_postgres_connection.py`
- `scripts/phase10_dry_run_migration.py`
- `docs/testing/PHASE_TESTING_STANDARD.md`

## Tasks

1. Activate PostgreSQL dry-run container with `docker-compose.phase10-dryrun.yml`.
2. Update setup guide with connection configuration details.
3. Verify `.env.dryrun.example`.
4. Validate PostgreSQL connection.
5. Improve safety tests.
6. Create `docs/migration/POSTGRESQL_DRY_RUN_VALIDATION_REPORT.md`.
7. Run required tests.
8. Create review package.

## Git Requirements

Branch:

```text
migration/phase-10.2.1.1-postgresql-activation
```

Commit:

```text
chore: activate postgresql dry run environment
```

Tag:

```text
phase-10.2.1.1-postgresql-ready
```

## Final Status

WAITING FOR ARCHITECT REVIEW

Do not start Phase 10.2 rerun or Phase 10.3.
