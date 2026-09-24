# PostgreSQL Dry Run Environment

## Phase

Phase 10.2.1 - PostgreSQL Dry Run Environment Setup

## Purpose

This environment is only for migration simulation. It is a safe target for
running Phase 10.2 dry-run checks before any real database ownership transfer.

## PostgreSQL Version Requirement

Use PostgreSQL 16 or newer for local dry-run validation.

PostgreSQL 15 is acceptable for compatibility checks, but the target design
should be reviewed again if production later chooses a different major version.

## Database Naming Convention

The database name must clearly indicate that it is not production.

Allowed examples:

- `mecprecision_dryrun`
- `mecprecision_test`
- `mecprecision_staging`
- `mecprecision_dev`

Rejected examples:

- `mecprecision_prod`
- `mecprecision_production`
- `mecprecision_live`
- `postgres`
- `template0`
- `template1`

The safety validator rejects names containing production/live markers even if a
dry-run marker is also present.

## User And Permission Requirement

Use a dedicated dry-run database user.

Minimum permissions:

- connect to the dry-run database
- create temporary objects
- use the `public` schema
- create objects in the `public` schema

Do not use a production application user, DBA superuser or shared production
credential for dry-run work.

## Connection Configuration

Configure the dry-run URL with:

```powershell
$env:PHASE10_DRY_RUN_DATABASE_URL = "postgresql://dryrun_user:password@localhost:5432/mecprecision_dryrun"
```

For local development, copy:

```text
.env.dryrun.example
```

to:

```text
.env.dryrun
```

Then replace the example password.

## Environment Variables

| Variable | Purpose | Required |
|---|---|---|
| `PHASE10_DRY_RUN_DATABASE_URL` | Non-production PostgreSQL target for migration dry run | Yes |

## Optional Docker Environment

This phase adds a local-only Docker Compose file:

```powershell
docker compose -f docker-compose.phase10-dryrun.yml up -d
```

If your Docker installation uses the older standalone Compose command, use:

```powershell
docker-compose -f docker-compose.phase10-dryrun.yml up -d
```

It creates a PostgreSQL container named:

```text
mecprecision_phase10_dryrun_postgres
```

The compose file is for local simulation only. It is not a production deployment
definition.

## Safety Rules

- Never point `PHASE10_DRY_RUN_DATABASE_URL` to a production database.
- Never use database names containing `prod`, `production` or `live`.
- Never run ownership transfer from this phase.
- Never write to `backend/database/mecprecision.sqlite`.
- Keep `.env.dryrun` out of Git.
- Commit only `.env.dryrun.example`.

## Validation Command

Run:

```powershell
python scripts/check_phase10_postgres_connection.py
```

If no URL is configured, the script reports `not_configured` and does not
attempt a PostgreSQL connection.

When the URL is configured, the script validates:

- URL scheme
- safe database name
- forbidden production markers
- PostgreSQL connectivity
- PostgreSQL version
- required permissions
