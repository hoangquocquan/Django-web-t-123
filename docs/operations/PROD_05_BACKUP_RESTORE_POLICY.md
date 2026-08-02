# PROD-05 Backup and Restore Policy

## Coverage

`python scripts/prod05_backup.py` creates a custom-format PostgreSQL dump, media archive, encrypted n8n runtime archive, versioned n8n workflow archive, and release manifest. The PostgreSQL dump includes Django and n8n database rows because both currently use the project PostgreSQL service.

## Schedule

- Daily backup: retain 14 days.
- Weekly backup: retain 8 weeks.
- Monthly backup: retain 12 months.
- Run an isolated restore test after every release and at least monthly.

The production scheduler and off-host encrypted storage require separate human-approved infrastructure configuration. Local output defaults to the Git-ignored `backups/prod05/` directory.

## Recovery Objectives

- Target RPO: 24 hours until continuous backup is introduced.
- Target RTO: 4 hours, validated by the isolated restore test.

## Integrity

Every component has SHA-256 in `release-manifest.json`. Restore stops on a missing file, checksum mismatch, malformed safety gate, unsafe archive path, migration drift, or failed database smoke check.
