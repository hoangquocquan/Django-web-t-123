# Isolated Restore

1. Create a fresh backup with `python scripts/prod05_backup.py` and copy the printed package path.
2. Run `python scripts/prod05_restore_test.py <package> --output <safe-report-path>`.
3. Confirm checksum validation, temporary media/n8n extraction, migration check, and database smoke test are PASS.
4. Confirm the temporary restore database was removed and `production_data_modified` is false.
5. A real production restore requires incident-owner and data-owner approval; this script never performs it.
