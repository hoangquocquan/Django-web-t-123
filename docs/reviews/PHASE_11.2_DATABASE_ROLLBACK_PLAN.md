# Phase 11.2 Database Rollback Plan

## Restore Point

The restore point is the backup file created by:

```powershell
python scripts\phase11_2_database_archive_backup.py
```

The backup location is recorded in:

`docs/migration/database_archive/archive_metadata.json`

## Restore Procedure

1. Confirm the restore request is approved by the technical owner.
2. Copy the archived SQLite file to a temporary restore location.
3. Verify the SHA-256 checksum before opening the file.
4. Open the restored copy in read-only mode.
5. Run SQLite `PRAGMA integrity_check`.
6. Compare row counts for critical tables.
7. Only after validation, decide whether any runtime should point to the
   restored database.

## Validation After Restore

Required checks:

- archive checksum matches metadata
- database opens successfully
- integrity check returns `ok`
- business-critical tables are readable
- original production database remains untouched

## Emergency Scenario

If a future production archive or restore fails:

1. Stop the restore attempt.
2. Keep the current production database online.
3. Escalate to the database owner and rollback owner.
4. Use the last known verified archive.
5. Open a corrective minor phase before retrying.

## Safety Notes

- Do not overwrite `backend/database/mecprecision.sqlite` during this training
  phase.
- Do not delete backup files until retention is approved.
- Do not commit `.sqlite` archive files to Git.
