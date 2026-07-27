# Phase 11.2 Database Archive Plan

## Objective

Create a lightweight archive workflow for the legacy SQLite database after the
training Legacy API shutdown exercise.

This phase is for training and governance only. It does not delete the legacy
database and does not modify any production database.

## Database Scope

| Item | Value |
| --- | --- |
| Database name | `mecprecision.sqlite` |
| Source location | `backend/database/mecprecision.sqlite` |
| Engine | SQLite |
| Environment | `TRAINING` |
| Archive type | `LEGACY_DATABASE_ARCHIVE` |

## Backup Strategy

1. Read the source SQLite database in read-only mode.
2. Copy the database into `docs/migration/database_archive/backup/`.
3. Calculate a SHA-256 checksum for the copied file.
4. Generate metadata and checkpoint records.
5. Keep the original database unchanged.

The copied `.sqlite` file is intentionally ignored by Git because database
archives may contain sensitive business data.

## Archive Strategy

The archive package is represented by:

- backup SQLite copy in `backup/`
- checksum file in `backup/`
- archive metadata in `archive_metadata.json`
- package manifest in `metadata/`
- verification report in `reports/`

## Verification Method

The verification tool checks:

- backup file exists
- metadata exists
- checksum matches the backup file
- SQLite archive can be opened in read-only mode
- SQLite `PRAGMA integrity_check` returns `ok`

## Rollback Strategy

Rollback means restoring from the archived copy if the legacy database must be
used again for investigation or emergency recovery. The restore process must
copy the archived file to a separate restore location first, then validate it
before any operator points a runtime at it.

## Retention Policy

For training:

- keep archive metadata and reports in Git
- keep database archive files outside Git
- review retention after Phase 12 planning

For production later:

- store encrypted archives in approved backup storage
- define owner, retention period and restore test schedule
- record every access in the audit log
