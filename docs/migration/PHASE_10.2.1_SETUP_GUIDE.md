# Phase 10.2.1 Setup Guide

## Step 1: Install PostgreSQL

Install PostgreSQL 16 or use Docker Desktop.

Docker option:

```powershell
docker compose -f docker-compose.phase10-dryrun.yml up -d
```

Fallback for older Docker Compose installations:

```powershell
docker-compose -f docker-compose.phase10-dryrun.yml up -d
```

## Step 2: Create Dry-Run Database

Required database name examples:

- `mecprecision_dryrun`
- `mecprecision_test`
- `mecprecision_staging`

Do not use names such as:

- `mecprecision_prod`
- `mecprecision_production`
- `mecprecision_live`

## Step 3: Configure Environment Variable

Copy the example file:

```powershell
Copy-Item .env.dryrun.example .env.dryrun
```

Edit `.env.dryrun` and replace the password.

Temporary PowerShell option:

```powershell
$env:PHASE10_DRY_RUN_DATABASE_URL = "postgresql://dryrun_user:password@localhost:5432/mecprecision_dryrun"
```

## Step 4: Run Connection Test

Run:

```powershell
python scripts/check_phase10_postgres_connection.py
```

Expected when database is ready:

```text
"status": "ready"
```

Expected when URL is not configured:

```text
"status": "not_configured"
```

This is safe because no database connection is attempted.

## Step 5: Execute Phase 10.2 Dry Run

After the connection test returns `ready`, rerun:

```powershell
python scripts/phase10_dry_run_migration.py
```

Expected:

```text
"dry_run_allowed": true
```

This still does not import production data or transfer ownership. It only clears
the environment safety gate for the next migration dry-run step.

## Troubleshooting

If the validator returns `blocked`, check:

- URL starts with `postgresql://` or `postgres://`
- database name includes `dryrun`, `test`, `staging` or `dev`
- database name does not include `prod`, `production` or `live`
- PostgreSQL container/service is running
- username and password are correct
- user can create objects in the dry-run database
